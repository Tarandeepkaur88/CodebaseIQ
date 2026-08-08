import os
from typing import TypedDict, Optional

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END

from backend.services.qa_agent import answer_question
from backend.services.bug_agent import analyze_code
from backend.services.docs_agent import generate_docs


load_dotenv()


class AgentState(TypedDict):
    repo_url: str
    message: str
    intent: Optional[str]
    result: Optional[dict]


def route_intent(state: AgentState) -> AgentState:
    """
    Router node — asks Groq to classify the user's message into:
    qa, bug, or docs.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    prompt = f"""
Classify the user's request into exactly ONE category:

- "qa" — if they are asking a question about the code,
  how something works, what something does, etc.

- "bug" — if they want bugs, issues, vulnerabilities,
  security problems, or code review.

- "docs" — if they want documentation or a written
  technical explanation/summary generated.

User request:
"{state['message']}"

Respond with ONLY one word:
qa, bug, or docs
"""

    completion = Groq(
        api_key=api_key
    ).chat.completions.create(
        model="llama-3.3-70b-versatile",

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

    if intent not in (
        "qa",
        "bug",
        "docs"
    ):
        intent = "qa"

    state["intent"] = intent

    print(
        f"\nRouter selected agent: {intent}"
    )

    return state


def run_qa_agent(
    state: AgentState
) -> AgentState:

    state["result"] = answer_question(
        repo_url=state["repo_url"],
        question=state["message"],
        limit=10
    )

    return state


def run_bug_agent(
    state: AgentState
) -> AgentState:

    # IMPORTANT:
    # Bug Finder now scans the repository in batches.
    # Therefore it no longer uses limit=10.

    state["result"] = analyze_code(
        repo_url=state["repo_url"],
        question=state["message"]
    )

    return state


def run_docs_agent(
    state: AgentState
) -> AgentState:

    state["result"] = generate_docs(
        repo_url=state["repo_url"],
        target=state["message"],
        limit=10
    )

    return state


def decide_next_node(
    state: AgentState
) -> str:
    """
    Tells LangGraph which agent to execute
    after the router.
    """

    return state["intent"]


# ============================================================
# BUILD LANGGRAPH
# ============================================================

graph = StateGraph(
    AgentState
)


# Nodes

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


# Entry point

graph.set_entry_point(
    "router"
)


# Router → Agent

graph.add_conditional_edges(
    "router",
    decide_next_node,
    {
        "qa": "qa",
        "bug": "bug",
        "docs": "docs",
    }
)


# Agent → End

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


# Compile graph

app_graph = graph.compile()


# ============================================================
# MAIN REQUEST HANDLER
# ============================================================

def handle_request(
    repo_url: str,
    message: str
) -> dict:
    """
    Main entry point.

    The user sends a message and LangGraph decides
    which specialized agent should handle it.
    """

    initial_state: AgentState = {
        "repo_url": repo_url,
        "message": message,
        "intent": None,
        "result": None,
    }

    final_state = app_graph.invoke(
        initial_state
    )

    return {
        "intent": final_state["intent"],
        "result": final_state["result"],
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    tests = [
        "What does this project do?",

        "Are there any bugs or security issues?",

        "Generate documentation for the database functions",
    ]

    for test_message in tests:

        print("\n===================================")

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

        print(
            "Routed to:",
            output["intent"]
        )

        if output["result"]:

            print(
                "Result keys:",
                list(
                    output["result"].keys()
                )
            )