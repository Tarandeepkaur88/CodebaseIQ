"""Retrieval-augmented documentation generation agent."""

import os

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
            "file": metadata.get(
                "file"
            ),
            "start_line": metadata.get(
                "start_line"
            ),
            "end_line": metadata.get(
                "end_line"
            ),
        }

        key = (
            source["file"],
            source["start_line"],
            source["end_line"],
        )

        if key not in seen:

            seen.add(key)

            sources.append(
                source
            )

    return sources


# ============================================================
# GET README
# ============================================================

def _get_readme(
    search: RepositorySearch,
    repo_url: str
) -> list[dict]:

    documentation = []

    readme_names = [
        "README.md",
        "README.rst",
        "readme.md",
        "readme.rst",
    ]

    for name in readme_names:

        try:

            matches = search.get_file_chunks(
                repo_url,
                name
            )

            if matches:

                documentation.extend(
                    matches
                )

                print(
                    f"Found documentation: {name}"
                )

                break

        except Exception as exc:

            print(
                f"Could not retrieve "
                f"{name}: {exc}"
            )

    return documentation


# ============================================================
# GENERATE DOCUMENTATION
# ============================================================

def generate_docs(
    repo_url: str,
    target: str = None,
    limit: int = 8
) -> dict:

    search = RepositorySearch()

    # ========================================================
    # PROJECT-LEVEL DOCUMENTATION
    # ========================================================

    is_project_documentation = (
        target is None
        or
        target.strip().lower()
        in {
            "project",
            "whole project",
            "entire project",
            "complete project",
            "overview",
            "project overview",
        }
    )

    # ========================================================
    # RETRIEVE README + CODE
    # ========================================================

    if is_project_documentation:

        print(
            "\nGenerating documentation "
            "for the entire project."
        )

        # README
        readme_matches = _get_readme(
            search,
            repo_url
        )

        # Relevant code
        code_matches = search.query(
            repo_url,
            "main functionality architecture "
            "components modules workflow",
            limit=limit
        )

        matches = (
            readme_matches
            + code_matches
        )

        retrieval_mode = "project"

    # ========================================================
    # SPECIFIC MODULE / FILE
    # ========================================================

    else:

        print(
            f"\nGenerating documentation for: "
            f"{target}"
        )

        matches = search.query(
            repo_url,
            target,
            limit=limit
        )

        retrieval_mode = "specific"

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique_matches = []
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

            unique_matches.append(
                match
            )

    matches = unique_matches

    # ========================================================
    # NO RESULTS
    # ========================================================

    if not matches:

        return {
            "target": target,

            "documentation": (
                "No indexed repository content "
                "was found. Please index the "
                "repository first."
            ),

            "sources": [],
        }

    # ========================================================
    # BUILD CONTEXT
    # ========================================================

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

        source_type = metadata.get(
            "source",
            "code"
        )

        content = match.get(
            "text",
            ""
        )

        context_blocks.append(
            f"""
FILE: {file_name}

LINES: {start_line}-{end_line}

SOURCE TYPE: {source_type}

CONTENT:
{content}
"""
        )

    context = (
        "\n\n"
        "================================================"
        "\n\n"
    ).join(context_blocks)

    # ========================================================
    # PROJECT DOCUMENTATION PROMPT
    # ========================================================

    if retrieval_mode == "project":

        instructions = """
You are generating documentation for an
ENTIRE SOFTWARE PROJECT.

You have two types of evidence:

1. DOCUMENTATION
   Such as README.md.

2. IMPLEMENTATION
   Actual source code.

This distinction is extremely important.

The README may describe intended or planned
features that are not actually implemented.

Therefore, divide your documentation into:

## Documentation Claims

Explain what the README/documentation says
the project is intended to do.

## Implementation Evidence

Explain what the supplied source code actually
implements.

## Implementation Gaps

If the README claims functionality that cannot
be verified from the supplied source code,
explicitly list it here.

For example:

- README claims remote watering.
- Source code shows no API communication.
- Therefore remote watering is NOT verified.

Never turn a README claim into an implementation
fact.

Use phrases such as:

"According to the README..."

"The inspected source code implements..."

"The provided repository content does not
provide evidence of..."

This makes the documentation trustworthy.
"""

        target_title = (
            "Entire Project"
        )

    # ========================================================
    # SPECIFIC MODULE PROMPT
    # ========================================================

    else:

        instructions = """
You are documenting a specific module or
component of a software project.

Use ONLY the supplied implementation evidence.

Explain:

- What the module does
- Important functions
- Classes
- Inputs
- Outputs
- Dependencies
- Control flow
- Error handling
- Security considerations
- Usage

Do NOT invent functionality.

If something cannot be determined from the
supplied code, explicitly say so.
"""

        target_title = target

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are a Senior Software Engineer and
Technical Documentation Specialist.

Your job is to create accurate developer
documentation for CodebaseIQ.

TARGET:
{target_title}

{instructions}

IMPORTANT RULES:

- Use ONLY the supplied repository content.
- Do not invent files.
- Do not invent APIs.
- Do not invent classes.
- Do not invent functions.
- Do not assume README claims are implemented.
- Mention file names and line ranges.
- Clearly distinguish documentation from code.
- If implementation evidence is missing,
  explicitly say so.
- Write professional Markdown.
- Be technically precise.

REPOSITORY CONTENT:

{context}


Generate documentation using this structure:

# Overview

Explain the project's/module's purpose.

# Documentation Claims

Explain functionality described by README or
other documentation.

# Implementation Evidence

Explain what the actual source code implements.

# Architecture

Describe the components that are actually
supported by the supplied repository content.

# Key Components

For each important component include:

- Name
- File
- Line range
- Purpose
- Inputs
- Outputs
- Implementation details

# Workflow

Explain the actual execution flow supported
by the code.

# Dependencies

List libraries, frameworks and modules that
are actually visible in the repository content.

# Error Handling

Describe actual error handling.

If none is present, say so.

# Security Considerations

Describe actual security mechanisms or
security-relevant code.

Do NOT invent vulnerabilities.

# Implementation Gaps

List functionality mentioned in documentation
but not supported by the inspected source code.

# Usage Example

Provide a usage example only when supported
by the code.

# Summary

Give a concise and accurate summary.

Remember:

DOCUMENTATION CLAIM ≠ IMPLEMENTATION FACT.
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

                model=
                    "llama-3.3-70b-versatile",

                messages=[
                    {
                        "role":
                            "user",

                        "content":
                            prompt,
                    }
                ],

                temperature=0.2,

                max_tokens=3000,
            )
        )

        documentation = (
            completion
            .choices[0]
            .message
            .content
        )

    except Exception as exc:

        return {
            "target": target,

            "documentation":
                f"Error generating documentation: {exc}",

            "sources":
                _sources(matches),
        }

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "target":
            target,

        "documentation":
            documentation,

        "sources":
            _sources(matches),
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = generate_docs(
        repo_url=
            "https://github.com/Tarandeepkaur88/ReZniX",

        target=None
    )

    print(
        "\n========== DOCUMENTATION ==========\n"
    )

    print(
        result["documentation"]
    )

    print(
        "\n========== SOURCES ==========\n"
    )

    for source in result["sources"]:

        print(source)