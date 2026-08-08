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
        metadata = match.get("metadata", {})

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
# FILE NAME DETECTION
# ============================================================

def _extract_filename(question: str) -> str | None:

    # Example:
    # Explain `main.js`

    pattern = (
        r"`([^`]+\.(?:py|js|jsx|ts|tsx|java|go|rb|cpp|c|h|hpp|"
        r"cs|php|rs|sql|md|rst))`"
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
        r"\b([A-Za-z0-9_./\\-]+\.(?:py|js|jsx|ts|tsx|java|go|rb|"
        r"cpp|c|h|hpp|cs|php|rs|sql|md|rst))\b"
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

def _is_project_overview(question: str) -> bool:

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

def _is_architecture_question(question: str) -> bool:

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
# BUILD CONTEXT
# ============================================================

def _build_context(
    matches: list[dict]
) -> str:

    context_parts = []

    for match in matches:

        metadata = match.get(
            "metadata",
            {}
        )

        file = metadata.get(
            "file",
            "unknown"
        )

        start = metadata.get(
            "start_line",
            "?"
        )

        end = metadata.get(
            "end_line",
            "?"
        )

        source_type = metadata.get(
            "source",
            "code"
        )

        content = match.get(
            "text",
            ""
        )

        context_parts.append(
            f"""
FILE: {file}
LINES: {start}-{end}
SOURCE TYPE: {source_type}

CONTENT:
{content}
"""
        )

    return (
        "\n\n"
        "=========================================="
        "\n\n"
    ).join(context_parts)


# ============================================================
# MAIN Q&A
# ============================================================

def answer_question(
    repo_url: str,
    question: str,
    limit: int = 10
) -> dict:

    search = RepositorySearch()

    matches = []
    retrieval_mode = "semantic"

    # ========================================================
    # CASE 1: SPECIFIC FILE QUESTION
    # ========================================================

    file_name = _extract_filename(
        question
    )

    if file_name:

        print(
            f"\nDetected file question: {file_name}"
        )

        matches = search.get_file_chunks(
            repo_url,
            file_name
        )

        retrieval_mode = "file-specific"

    # ========================================================
    # CASE 2: ARCHITECTURE / DATA FLOW
    # ========================================================

    elif _is_architecture_question(
        question
    ):

        print(
            "\nDetected architecture/data-flow question."
        )

        # ----------------------------------------------------
        # Get ALL source code
        # ----------------------------------------------------

        all_source_chunks = (
            search.get_all_source_chunks(
                repo_url
            )
        )

        # ----------------------------------------------------
        # Get README/documentation
        # ----------------------------------------------------

        documentation_chunks = []

        # Most repositories use README.md.
        # We also try README.rst.

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
                        docs
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
        # Find API/backend-related source code
        # ----------------------------------------------------

        keywords = [
            "fetch(",
            "axios",
            "xmlhttprequest",
            "http",
            "https",
            "api",
            "request",
            "response",
            "@app.",
            "@router.",
            "router.",
            "route",
            "post(",
            "get(",
            "put(",
            "delete(",
            "database",
            "supabase",
            "requests.",
            "fastapi",
            "flask",
            "express",
            "sql",
        ]

        relevant_source_chunks = []

        for chunk in all_source_chunks:

            text = chunk.get(
                "text",
                ""
            ).lower()

            if any(
                keyword.lower() in text
                for keyword in keywords
            ):

                relevant_source_chunks.append(
                    chunk
                )

        # ----------------------------------------------------
        # Combine documentation + relevant source
        # ----------------------------------------------------

        matches = (
            documentation_chunks
            + relevant_source_chunks[:60]
        )

        # If nothing matched the API keywords,
        # still provide some source code.
        if not relevant_source_chunks:

            matches = (
                documentation_chunks
                + all_source_chunks[:40]
            )

        retrieval_mode = "architecture"

        print(
            f"Architecture retrieval:"
            f" {len(matches)} chunks"
        )

    # ========================================================
    # CASE 3: PROJECT OVERVIEW
    # ========================================================

    elif _is_project_overview(
        question
    ):

        print(
            "\nDetected project overview question."
        )

        # First semantic search
        # This can retrieve README + source code
        # because README is now indexed.

        matches = search.query(
            repo_url,
            question,
            limit=limit
        )

        # Explicitly add README so project purpose
        # is not lost because of semantic ranking.

        documentation_chunks = []

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
                        docs
                    )

                    break

            except Exception:
                pass

        # README first, then semantic results.
        matches = (
            documentation_chunks
            + matches
        )

        # Remove duplicate chunks.
        unique = []
        seen = set()

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
                unique.append(match)

        matches = unique

        retrieval_mode = "project-overview"

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
    # DIFFERENT INSTRUCTIONS
    # ========================================================

    if retrieval_mode == "architecture":

        instruction = """
The user is asking about the architecture or
data flow of the repository.

You have been given BOTH documentation and
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

Use the README/documentation to explain:

- project purpose
- problem being solved
- intended users
- major features

Then use source code to explain what is
actually implemented.

VERY IMPORTANT:

Separate:

DOCUMENTATION CLAIMS
from
IMPLEMENTATION EVIDENCE.

If the README says something that is not
visible in the source code, say so.

Do not claim that a feature is implemented
just because the README mentions it.
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

- Be technically precise.
- Use actual repository evidence.
- Mention file names and line ranges.
- Do not hallucinate missing functionality.
- Clearly distinguish README claims from
  implementation evidence.
- If something is not present, explicitly
  say that it was not found.
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

                model="llama-3.3-70b-versatile",

                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],

                temperature=0.1,

                max_tokens=1800,
            )
        )

        answer = (
            completion
            .choices[0]
            .message
            .content
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