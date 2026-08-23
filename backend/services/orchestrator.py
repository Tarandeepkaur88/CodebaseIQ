import os
from typing import TypedDict, Optional

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END

from backend.services.qa_agent import answer_question
from backend.services.bug_agent import analyze_code
from backend.services.docs_agent import generate_docs


load_dotenv()


# ============================================================
# AGENT STATE
# ============================================================

class AgentState(TypedDict):
    repo_url: str
    message: str
    intent: Optional[str]
    result: Optional[dict]


# ============================================================
# ROUTER AGENT
# ============================================================

def route_intent(state: AgentState) -> AgentState:
    """
    Router node.

    First checks obvious keywords for deterministic routing.
    If the request is ambiguous, Groq classifies it.

    Possible intents:
    - qa
    - bug
    - docs
    """

    message = state["message"].lower()

    # ========================================================
    # FAST KEYWORD ROUTING
    # ========================================================

    bug_keywords = [
        "bug",
        "bugs",
        "issue",
        "issues",
        "security",
        "vulnerability",
        "vulnerabilities",
        "code review",
        "review my code",
        "review the code",
        "performance problem",
        "performance problems",
        "performance issue",
        "performance issues",
        "error",
        "errors",
        "broken",
        "problem",
        "problems",
    ]

    docs_keywords = [
        "documentation",
        "document",
        "generate docs",
        "generate documentation",
        "write docs",
        "write documentation",
        "technical documentation",
        "module documentation",
        "project documentation",
        "document this",
        "explain this module",
        "create documentation",
    ]

    # Check for BUG requests first
    if any(keyword in message for keyword in bug_keywords):

        intent = "bug"

        print("\nKeyword routing selected: BUG")

    # Check for DOCUMENTATION requests
    elif any(keyword in message for keyword in docs_keywords):

        intent = "docs"

        print("\nKeyword routing selected: DOCS")

    # ========================================================
    # LLM ROUTING FOR AMBIGUOUS REQUESTS
    # ========================================================

    else:

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured"
            )

        prompt = f"""
Classify the user's request into exactly ONE category.

Categories:

- "qa"
Use this when the user is asking about:
how code works,
what a function does,
project architecture,
data flow,
classes,
functions,
APIs,
implementation,
or general questions about the repository.

- "bug"
Use this when the user wants:
bugs,
issues,
errors,
security vulnerabilities,
performance problems,
code review,
or implementation problems.

- "docs"
Use this when the user wants:
documentation,
technical documentation,
module documentation,
project documentation,
or a structured written explanation.

User request:

"{state['message']}"

Respond with ONLY one word:

qa

bug

docs
"""

        completion = Groq(
            api_key=api_key
        ).chat.completions.create(

            model="qwen/qwen3.6-27b",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0,

            max_tokens=5
        )

        intent = (
            completion
            .choices[0]
            .message
            .content
            .strip()
            .lower()
        )

        # Safety fallback

        if intent not in (
            "qa",
            "bug",
            "docs"
        ):

            print(
                f"Invalid router response: {intent}"
            )

            intent = "qa"

    # Save selected intent

    state["intent"] = intent

    # Debug logs

    print("\n===================================")
    print("LANGGRAPH ROUTER")
    print(f"User request: {state['message']}")
    print(f"Selected intent: {intent}")
    print("===================================\n")

    return state


# ============================================================
# Q&A AGENT
# ============================================================

def run_qa_agent(
    state: AgentState
) -> AgentState:
    """
    Repository Q&A Agent.

    Retrieves relevant repository code and generates
    a grounded answer.
    """

    print(
        "\n>>> Running Repository Q&A Agent...\n"
    )

    state["result"] = answer_question(

        repo_url=state["repo_url"],

        question=state["message"],

        limit=10

    )

    return state


# ============================================================
# BUG FINDER AGENT
# ============================================================

def run_bug_agent(
    state: AgentState
) -> AgentState:
    """
    Bug Finder Agent.

    Analyzes repository code for:

    - Bugs
    - Security issues
    - Vulnerabilities
    - Performance problems
    - Implementation problems
    """

    print(
        "\n>>> Running Bug Finder Agent...\n"
    )

    state["result"] = analyze_code(

        repo_url=state["repo_url"],

        question=state["message"]

    )

    return state


# ============================================================
# DOCUMENTATION AGENT
# ============================================================

def run_docs_agent(
    state: AgentState
) -> AgentState:
    """
    Documentation Agent.

    Retrieves relevant repository code and generates
    structured technical documentation.
    """

    print(
        "\n>>> Running Documentation Agent...\n"
    )

    state["result"] = generate_docs(

        repo_url=state["repo_url"],

        target=state["message"],

        limit=10

    )

    return state


# ============================================================
# CONDITIONAL ROUTING
# ============================================================

def decide_next_node(
    state: AgentState
) -> str:
    """
    Tells LangGraph which specialized agent
    should execute after the Router Agent.
    """

    return state["intent"]


# ============================================================
# BUILD LANGGRAPH WORKFLOW
# ============================================================

graph = StateGraph(
    AgentState
)


# ============================================================
# ADD NODES
# ============================================================

graph.add_node(
    "router",
    route_intent
)

graph.add_node(
    "qa",
    run_qa_agent
)

graph.add_node(
    "bug",
    run_bug_agent
)

graph.add_node(
    "docs",
    run_docs_agent
)


# ============================================================
# ENTRY POINT
# ============================================================

graph.set_entry_point(
    "router"
)


# ============================================================
# ROUTER -> SPECIALIZED AGENT
# ============================================================

graph.add_conditional_edges(

    "router",

    decide_next_node,

    {
        "qa": "qa",

        "bug": "bug",

        "docs": "docs",
    }

)


# ============================================================
# SPECIALIZED AGENTS -> END
# ============================================================

graph.add_edge(
    "qa",
    END
)

graph.add_edge(
    "bug",
    END
)

graph.add_edge(
    "docs",
    END
)


# ============================================================
# COMPILE LANGGRAPH
# ============================================================

app_graph = graph.compile()


# ============================================================
# MAIN AGENT HANDLER
# ============================================================

def handle_request(
    repo_url: str,
    message: str
) -> dict:
    """
    Main entry point for the Agentic AI system.

    Workflow:

    User Message
         |
         v
    LangGraph Router
         |
         v
    Intent Classification
         |
    -------------------------
    |           |           |
    v           v           v
    QA Agent   Bug Agent   Docs Agent
    |           |           |
    v           v           v
    Answer    Analysis   Documentation
         |
         v
    Final Response
    """

    # Initial state

    initial_state: AgentState = {

        "repo_url": repo_url,

        "message": message,

        "intent": None,

        "result": None,

    }


    # ========================================================
    # RUN LANGGRAPH WORKFLOW
    # ========================================================

    final_state = app_graph.invoke(
        initial_state
    )


    # Get selected intent

    intent = final_state["intent"]


    # ========================================================
    # HUMAN-READABLE AGENT NAMES
    # ========================================================

    agent_names = {

        "qa": "Repository Q&A Agent",

        "bug": "Bug Finder Agent",

        "docs": "Documentation Agent",

    }


    selected_agent = agent_names.get(

        intent,

        "Repository Q&A Agent"

    )


    # ========================================================
    # RETURN FINAL RESULT
    # ========================================================

    return {

        "intent": intent,

        "agent": selected_agent,

        "workflow": {

            "framework": "LangGraph",

            "router": "Intent Router",

            "selected_agent": selected_agent,

            "status": "completed",

        },

        "result": final_state["result"],

    }


# ============================================================
# LOCAL TESTING
# ============================================================

if __name__ == "__main__":

    tests = [

        "What does this project do?",

        "Are there any bugs or security issues?",

        "Generate documentation for the database functions",

        "Explain how authentication works",

        "Review the code for vulnerabilities",

    ]


    for test_message in tests:

        print("\n")
        print("===================================")

        print(
            f"Message: {test_message}"
        )

        print("===================================")


        output = handle_request(

            repo_url=(
                "https://github.com/"
                "Vanshgupta3/GreenSync"
            ),

            message=test_message

        )


        print("\nFinal Intent:")

        print(
            output["intent"]
        )


        print("\nSelected Agent:")

        print(
            output["agent"]
        )


        print("\nWorkflow:")

        print(
            output["workflow"]
        )


        if output["result"]:

            print("\nResult Keys:")

            print(
                list(
                    output["result"].keys()
                )
            )

        print("\n===================================\n")