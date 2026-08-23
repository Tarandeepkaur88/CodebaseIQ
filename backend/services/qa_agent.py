"""Retrieval-augmented Q&A agent."""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from backend.services.search import RepositorySearch


load_dotenv()


# ============================================================
# SOURCE CITATIONS
# ============================================================

def _sources(matches: list[dict]) -> list[dict]:

    seen = set()
    sources = []

    for match in matches:

        metadata = match.get(
            "metadata",
            {}
        )

        source = {
            "file": metadata.get("file"),
            "start_line": metadata.get("start_line"),
            "end_line": metadata.get("end_line"),
        }

        key = (
            source["file"],
            source["start_line"],
            source["end_line"],
        )

        if key not in seen:

            seen.add(key)
            sources.append(source)

    return sources


# ============================================================
# CLEAN MODEL OUTPUT
# ============================================================

def clean_model_output(content: str) -> str:
    """
    Remove Qwen reasoning blocks such as:

    <think>
    internal reasoning
    </think>

    Only the final answer should reach the frontend.
    """

    if not content:
        return ""

    content = content.strip()

    # Remove complete think blocks
    content = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return content.strip()


# ============================================================
# FILE NAME DETECTION
# ============================================================

def _extract_filename(
    question: str
) -> str | None:

    # Example:
    # Explain `main.js`

    pattern = (
        r"`([^`]+\.(?:py|js|jsx|mjs|cjs|ts|tsx|"
        r"html|htm|css|scss|sass|less|json|yaml|yml|xml|"
        r"java|go|rb|cpp|c|h|hpp|cs|php|rs|sql|md|rst))`"
    )

    match = re.search(
        pattern,
        question,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    # Example:
    # Explain main.js

    pattern = (
        r"\b([A-Za-z0-9_./\\-]+\.(?:py|js|jsx|mjs|cjs|"
        r"ts|tsx|html|htm|css|scss|sass|less|json|yaml|yml|xml|"
        r"java|go|rb|cpp|c|h|hpp|cs|php|rs|sql|md|rst))\b"
    )

    match = re.search(
        pattern,
        question,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# PROJECT OVERVIEW DETECTION
# ============================================================

def _is_project_overview(
    question: str
) -> bool:

    q = question.lower()

    phrases = [

        "what is this project",
        "what does this project do",
        "what is this project about",
        "explain this project",
        "project overview",
        "give me an overview",
        "purpose of this project",
        "what is the purpose",
        "what does the application do",
        "what does the app do",

    ]

    return any(
        phrase in q
        for phrase in phrases
    )


# ============================================================
# ARCHITECTURE / DATA FLOW DETECTION
# ============================================================

def _is_architecture_question(
    question: str
) -> bool:

    q = question.lower()

    phrases = [

        "data flow",
        "frontend to backend",
        "backend to frontend",
        "how does data flow",
        "how does the frontend communicate",
        "how does frontend communicate",
        "how does the backend work",
        "how do frontend and backend",
        "api flow",
        "request flow",
        "architecture",
        "system architecture",
        "how are the components connected",
        "how do the components interact",
        "how does the system work",

    ]

    return any(
        phrase in q
        for phrase in phrases
    )


# ============================================================
# REMOVE DUPLICATE MATCHES
# ============================================================

def _deduplicate_matches(
    matches: list[dict]
) -> list[dict]:

    seen = set()
    unique_matches = []

    for match in matches:

        metadata = match.get(
            "metadata",
            {}
        )

        key = (
            metadata.get("file"),
            metadata.get("start_line"),
            metadata.get("end_line"),
        )

        if key not in seen:

            seen.add(key)

            unique_matches.append(
                match
            )

    return unique_matches


# ============================================================
# BUILD CONTEXT
# ============================================================

def _build_context(
    matches: list[dict]
) -> str:

    context_blocks = []

    for match in matches:

        metadata = match.get(
            "metadata",
            {}
        )

        file_name = metadata.get(
            "file",
            "unknown"
        )

        start_line = metadata.get(
            "start_line",
            "?"
        )

        end_line = metadata.get(
            "end_line",
            "?"
        )

        content = match.get(
            "text",
            ""
        )

        context_blocks.append(
            f"""
FILE: {file_name}

LINES: {start_line}-{end_line}

CONTENT:

{content}
"""
        )

    return "\n\n====================\n\n".join(
        context_blocks
    )


# ============================================================
# MAIN Q&A AGENT
# ============================================================

def answer_question(
    repo_url: str,
    question: str,
    limit: int = 10,
) -> dict:

    search = RepositorySearch()

    matches = []
    retrieval_mode = "semantic"
    file_name = None

    # ========================================================
    # CASE 1: FILE-SPECIFIC QUESTION
    # ========================================================

    file_name = _extract_filename(
        question
    )

    if file_name:

        print(
            f"\nDetected file-specific question: "
            f"{file_name}"
        )

        try:

            matches = search.get_file_chunks(
                repo_url,
                file_name
            )

        except Exception as exc:

            print(
                f"File retrieval failed: {exc}"
            )

            matches = []

        retrieval_mode = "file-specific"


    # ========================================================
    # CASE 2: ARCHITECTURE / DATA FLOW
    # ========================================================

    elif _is_architecture_question(
        question
    ):

        print(
            "\nDetected architecture/data flow question."
        )

        matches = search.query(
            repo_url,
            question,
            limit=limit
        )

        retrieval_mode = "architecture"


    # ========================================================
    # CASE 3: PROJECT OVERVIEW
    # ========================================================

    elif _is_project_overview(
        question
    ):

        print(
            "\nDetected project overview question."
        )

        documentation_chunks = []

        # ----------------------------------------------------
        # 1. Semantic matches
        # ----------------------------------------------------

        semantic_matches = search.query(
            repo_url,
            question,
            limit=limit
        )

        # ----------------------------------------------------
        # 2. Try README
        # ----------------------------------------------------

        for readme_name in [

            "README.md",
            "README.rst",
            "readme.md",
            "readme.rst",

        ]:

            try:

                docs = search.get_file_chunks(
                    repo_url,
                    readme_name
                )

                if docs:

                    documentation_chunks.extend(
                        docs[:4]
                    )

                    print(
                        f"Found documentation: "
                        f"{readme_name}"
                    )

                    break

            except Exception as exc:

                print(
                    f"Could not retrieve "
                    f"{readme_name}: {exc}"
                )

        # ----------------------------------------------------
        # 3. Get all source chunks
        # ----------------------------------------------------

        all_source_chunks = (
            search.get_all_source_chunks(
                repo_url
            )
        )

        # ----------------------------------------------------
        # 4. Group chunks by file
        # ----------------------------------------------------

        grouped_by_file = {}

        for chunk in all_source_chunks:

            metadata = chunk.get(
                "metadata",
                {}
            )

            file_path = metadata.get(
                "file",
                ""
            )

            if not file_path:
                continue

            if file_path not in grouped_by_file:

                grouped_by_file[
                    file_path
                ] = []

            grouped_by_file[
                file_path
            ].append(
                chunk
            )

        # ----------------------------------------------------
        # 5. Prioritize important files
        # ----------------------------------------------------

        important_names = {

            "app.py",
            "main.py",
            "server.py",
            "server.js",
            "server.mjs",
            "index.js",
            "index.ts",
            "package.json",
            "requirements.txt",
            "config.py",

        }

        selected_chunks = []
        selected_files = set()

        # ----------------------------------------------------
        # 6. Important root/application files
        # ----------------------------------------------------

        for file_path, file_chunks in (
            grouped_by_file.items()
        ):

            normalized = file_path.replace(
                "\\",
                "/"
            )

            file_name_only = (
                normalized
                .split("/")[-1]
                .lower()
            )

            if file_name_only in {
                name.lower()
                for name in important_names
            }:

                selected_chunks.extend(
                    file_chunks[:1]
                )

                selected_files.add(
                    normalized.lower()
                )

        # ----------------------------------------------------
        # 7. Representative nested files
        # ----------------------------------------------------

        directory_limits = {

            "templates/": 5,
            "utils/": 4,
            "services/": 3,
            "routes/": 3,
            "controllers/": 3,
            "components/": 3,
            "pages/": 3,

        }

        for directory, max_files in (
            directory_limits.items()
        ):

            count = 0

            for file_path, file_chunks in (
                grouped_by_file.items()
            ):

                normalized = (
                    file_path
                    .replace("\\", "/")
                    .lower()
                )

                if not normalized.startswith(
                    directory
                ):
                    continue

                if normalized in selected_files:
                    continue

                selected_chunks.append(
                    file_chunks[0]
                )

                selected_files.add(
                    normalized
                )

                count += 1

                if count >= max_files:
                    break

        # ----------------------------------------------------
        # 8. Add semantic matches
        # ----------------------------------------------------

        selected_chunks.extend(
            semantic_matches[:5]
        )

        # ----------------------------------------------------
        # 9. Hard limit
        # ----------------------------------------------------

        selected_chunks = (
            selected_chunks[:20]
        )

        # ----------------------------------------------------
        # 10. Combine documentation + source
        # ----------------------------------------------------

        matches = (
            documentation_chunks
            + selected_chunks
        )

        # ----------------------------------------------------
        # 11. Remove duplicates
        # ----------------------------------------------------

        matches = _deduplicate_matches(
            matches
        )

        retrieval_mode = "project-overview"

        print(
            f"Project overview retrieval: "
            f"{len(matches)} chunks from "
            f"{len(grouped_by_file)} source files."
        )


    # ========================================================
    # CASE 4: NORMAL SEMANTIC SEARCH
    # ========================================================

    else:

        print(
            "\nUsing semantic search."
        )

        matches = search.query(
            repo_url,
            question,
            limit=limit
        )

        retrieval_mode = "semantic"


    # ========================================================
    # NO RESULTS
    # ========================================================

    if not matches:

        return {
            "question": question,

            "answer": (
                "I couldn't find relevant information "
                "in the indexed repository."
            ),

            "sources": [],
        }


    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    context = _build_context(
        matches
    )


    # ========================================================
    # AGENT INSTRUCTIONS
    # ========================================================

    if retrieval_mode == "architecture":

        instruction = """
The user is asking about the architecture or
data flow of the repository.

You have been given documentation and
source-code evidence.

Determine what the project claims to do and
what the source code actually implements.

For frontend-to-backend questions, inspect
the source code for:

- fetch()
- axios
- XMLHttpRequest
- HTTP requests
- API endpoints
- FastAPI routes
- Flask routes
- Express routes
- database calls
- Supabase calls
- backend services

If an actual flow exists, explain:

Frontend
→ API/request
→ Backend route
→ Service/business logic
→ Database/external service
→ Response
→ Frontend

For every step, mention the actual file
and line range.

If no frontend-to-backend communication
exists, clearly say:

"No frontend-to-backend communication was
found in the indexed source code."

Then explain:

1. What the README/documentation claims.
2. What the source code actually implements.
3. Any gap between the two.

IMPORTANT:

Never invent a backend, API, database,
sensor integration, or data flow that is
not supported by the source code.
"""

    elif retrieval_mode == "file-specific":

        instruction = f"""
The user specifically wants to understand:

{file_name}

Explain the actual implementation in this file.

Explain important:

- functions
- classes
- variables
- dependencies
- control flow
- responsibilities

Use the supplied code only.

Do not invent functionality.
"""

    elif retrieval_mode == "project-overview":

        instruction = """
The user wants to understand the project
at a high level.

You have been given:

1. README/documentation
2. Semantic search results
3. Representative source files from
   different parts of the repository

Use the README/documentation to explain:

- project purpose
- problem being solved
- intended users
- major features

Then use the source code to explain what is
actually implemented.

VERY IMPORTANT:

Separate:

DOCUMENTATION CLAIMS

from

IMPLEMENTATION EVIDENCE.

If the README claims a feature but the
supplied source evidence does not verify it,
say:

"No implementation evidence was found in
the retrieved source code."

Do NOT say that a feature definitely does
not exist merely because one file was not
retrieved.

Look at evidence from nested folders such as:

- templates/
- utils/
- services/
- routes/
- components/
- pages/

For important features, mention the actual
file and line range.

Do not invent files, functions, APIs,
databases, routes, or behavior.

Be concise but useful.
"""

    else:

        instruction = """
Answer the user's question using the
provided repository content.

Prefer actual source-code evidence.

Do not invent files, functions, variables,
APIs, dependencies, or behavior.
"""


    # ========================================================
    # GROQ PROMPT
    # ========================================================

    prompt = f"""
You are CodebaseIQ, an AI codebase intelligence
system.

{instruction}

USER QUESTION:

{question}

REPOSITORY CONTENT:

{context}

RULES:

- Return ONLY the final answer.
- Do NOT include <think> tags.
- Do NOT reveal internal reasoning.
- Do NOT describe your thinking process.
- Be technically precise.
- Use actual repository evidence.
- Mention file names and line ranges.
- Do not hallucinate missing functionality.
- Clearly distinguish README claims from
  implementation evidence.
- If something cannot be verified from the
  supplied repository evidence, say so.
"""


    # ========================================================
    # GROQ
    # ========================================================

    try:

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "GROQ_API_KEY is not configured"
            )

        client = Groq(
            api_key=api_key
        )

        completion = (
            client
            .chat
            .completions
            .create(

                model="qwen/qwen3.6-27b",

                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],

                temperature=0.1,

                max_tokens=1200,
            )
        )

        raw_answer = (
            completion
            .choices[0]
            .message
            .content
        )

        # Clean Qwen reasoning before sending
        # the answer to the frontend
        answer = clean_model_output(
            raw_answer
        )

    except Exception as exc:

        return {
            "question": question,

            "answer": (
                f"Error generating answer: {exc}"
            ),

            "sources": _sources(matches),
        }


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "question": question,
        "answer": answer,
        "sources": _sources(matches),
    }