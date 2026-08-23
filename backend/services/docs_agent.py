"""Retrieval-augmented documentation generation agent."""

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
# CLEAN LLM RESPONSE
# ============================================================

def _clean_llm_response(content: str) -> str:
    """
    Remove internal reasoning such as:

    <think>
    ...
    </think>

    and return only the final documentation.
    """

    if not content:
        return ""

    content = content.strip()

    # Remove complete <think>...</think> blocks
    content = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Safety case: model starts with <think> but
    # does not properly close it.
    if content.lower().startswith("<think>"):

        closing_tag = content.lower().find("</think>")

        if closing_tag != -1:

            content = content[
                closing_tag + len("</think>"):
            ]

    return content.strip()


# ============================================================
# NORMALIZE TARGET
# ============================================================

def _normalize_target(target: str) -> str:
    """
    Convert natural-language requests into an actual
    filename/path.

    Examples:

        "explain server.mjs"
            -> "server.mjs"

        "explain the file server.mjs"
            -> "server.mjs"

        "document server.mjs"
            -> "server.mjs"

        "generate documentation for server.mjs"
            -> "server.mjs"

        "server.mjs"
            -> "server.mjs"
    """

    if not target:
        return ""

    target = target.strip()

    # Remove surrounding quotes/backticks
    target = target.strip("`'\" ")

    # Common natural-language prefixes
    patterns = [

        r"^explain\s+the\s+file\s+",
        r"^explain\s+file\s+",
        r"^explain\s+the\s+",
        r"^explain\s+",

        r"^document\s+the\s+file\s+",
        r"^document\s+file\s+",
        r"^document\s+the\s+",
        r"^document\s+",

        r"^generate\s+documentation\s+for\s+the\s+file\s+",
        r"^generate\s+documentation\s+for\s+",

        r"^generate\s+docs\s+for\s+the\s+file\s+",
        r"^generate\s+docs\s+for\s+",

        r"^docs\s+for\s+the\s+file\s+",
        r"^docs\s+for\s+",

        r"^documentation\s+for\s+the\s+file\s+",
        r"^documentation\s+for\s+",
    ]

    for pattern in patterns:

        cleaned = re.sub(
            pattern,
            "",
            target,
            flags=re.IGNORECASE,
        )

        if cleaned != target:

            target = cleaned.strip()

            break

    # Remove trailing punctuation
    target = target.strip("`'\" .,!?")

    return target


# ============================================================
# CHECK IF TARGET LOOKS LIKE AN ACTUAL FILENAME
# ============================================================

def _looks_like_filename(target: str) -> bool:
    """
    Returns True only if the target looks like a real file.
    """

    if not target:
        return False

    pattern = (
        r"\.(?:py|js|jsx|mjs|cjs|ts|tsx|"
        r"html|htm|css|scss|sass|less|json|yaml|yml|xml|"
        r"java|go|rb|cpp|c|h|hpp|cs|php|rs|sql|md|rst)$"
    )

    return bool(
        re.search(
            pattern,
            target.strip(),
            re.IGNORECASE,
        )
    )


# ============================================================
# GET README
# ============================================================

def _get_readme(
    search: RepositorySearch,
    repo_url: str,
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
                name,
            )

            if matches:

                documentation.extend(matches)

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
# CHECK WHETHER MATCH BELONGS TO TARGET
# ============================================================

def _match_is_target_file(
    match: dict,
    target: str,
) -> bool:

    metadata = match.get(
        "metadata",
        {},
    )

    file_name = str(
        metadata.get(
            "file",
            "",
        )
    )

    if not file_name:
        return False

    normalized_file = (
        file_name
        .replace("\\", "/")
        .strip()
        .lower()
    )

    normalized_target = (
        target
        .replace("\\", "/")
        .strip()
        .lower()
    )

    # Exact path
    if normalized_file == normalized_target:
        return True

    # Exact filename
    actual_filename = (
        normalized_file
        .split("/")[-1]
    )

    target_filename = (
        normalized_target
        .split("/")[-1]
    )

    if actual_filename == target_filename:
        return True

    # Target is a path ending in the actual file
    if normalized_file.endswith(
        "/" + normalized_target
    ):
        return True

    return False


# ============================================================
# GET SPECIFIC FILE
# ============================================================

def _get_specific_file(
    search: RepositorySearch,
    repo_url: str,
    target: str,
    limit: int = 8,
) -> list[dict]:

    """
    Retrieve the requested file.

    Strategy:

    1. Try exact file retrieval.
    2. If that fails, use semantic search.
    3. Filter semantic results so another file
       cannot accidentally be documented.
    """

    target = _normalize_target(target)

    if not target:
        return []

    print(
        f"Looking for exact file: {target}"
    )

    # --------------------------------------------------------
    # STEP 1: EXACT FILE SEARCH
    # --------------------------------------------------------

    try:

        matches = search.get_file_chunks(
            repo_url,
            target,
        )

        if matches:

            print(
                f"Exact file found: {target}"
            )

            return matches

    except Exception as exc:

        print(
            f"Exact file lookup failed: {exc}"
        )

    # --------------------------------------------------------
    # STEP 2: SEMANTIC SEARCH FALLBACK
    # --------------------------------------------------------

    print(
        f"Exact file lookup did not find "
        f"{target}."
    )

    print(
        "Trying semantic search as fallback..."
    )

    try:

        matches = search.query(
            repo_url,
            target,
            limit=limit,
        )

    except Exception as exc:

        print(
            f"Semantic search failed: {exc}"
        )

        return []

    # --------------------------------------------------------
    # STEP 3: FILTER RESULTS
    # --------------------------------------------------------

    filtered_matches = []

    for match in matches:

        if _match_is_target_file(
            match,
            target,
        ):

            filtered_matches.append(
                match
            )

    if filtered_matches:

        print(
            f"Found {len(filtered_matches)} "
            f"matching chunks for {target}"
        )

        return filtered_matches

    # Do not return unrelated semantic results
    return []


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def _remove_duplicates(
    matches: list[dict],
) -> list[dict]:

    unique_matches = []

    seen = set()

    for match in matches:

        metadata = match.get(
            "metadata",
            {},
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
    matches: list[dict],
) -> str:

    context_blocks = []

    for match in matches:

        metadata = match.get(
            "metadata",
            {},
        )

        file_name = metadata.get(
            "file",
            "unknown",
        )

        start_line = metadata.get(
            "start_line",
            "?",
        )

        end_line = metadata.get(
            "end_line",
            "?",
        )

        source_type = metadata.get(
            "source",
            "code",
        )

        content = match.get(
            "text",
            "",
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

    return (
        "\n\n"
        "================================================"
        "\n\n"
    ).join(context_blocks)


# ============================================================
# GENERATE DOCUMENTATION
# ============================================================

def generate_docs(
    repo_url: str,
    target: str = None,
    limit: int = 8,
) -> dict:

    search = RepositorySearch()

    # ========================================================
    # DETERMINE DOCUMENTATION MODE
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

    is_specific_file = (

        not is_project_documentation

        and

        _looks_like_filename(
            _normalize_target(target)
        )

    )


    # ========================================================
    # PROJECT DOCUMENTATION
    # ========================================================

    if is_project_documentation:

        print(
            "\nGenerating documentation "
            "for the entire project."
        )

        readme_matches = _get_readme(
            search,
            repo_url,
        )

        code_matches = search.query(
            repo_url,
            (
                "main functionality "
                "architecture "
                "components "
                "modules "
                "workflow"
            ),
            limit=limit,
        )

        matches = (
            readme_matches
            + code_matches
        )

        retrieval_mode = "project"

        target_title = "Entire Project"


    # ========================================================
    # SPECIFIC FILE
    # ========================================================

    elif is_specific_file:

        original_target = target

        target = _normalize_target(
            target
        )

        print(
            "\nRequested target:",
            original_target,
        )

        print(
            "Normalized target:",
            target,
        )

        matches = _get_specific_file(
            search,
            repo_url,
            target,
            limit=limit,
        )

        retrieval_mode = "specific"

        target_title = target


    # ========================================================
    # TOPIC / GENERAL REQUEST
    # ========================================================

    else:

        original_target = target

        target = (
            _normalize_target(target)
            or original_target
        )

        print(
            f"\nTreating as topic: {target}"
        )

        readme_matches = _get_readme(
            search,
            repo_url,
        )

        code_matches = search.query(
            repo_url,
            target,
            limit=limit,
        )

        matches = (
            readme_matches
            + code_matches
        )

        retrieval_mode = "topic"

        target_title = target


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    matches = _remove_duplicates(
        matches
    )


    # ========================================================
    # NO RESULTS
    # ========================================================

    if not matches:

        if retrieval_mode == "specific":

            return {

                "target": target,

                "documentation": (
                    f"I could not find the requested "
                    f"file '{target}' in the indexed "
                    f"repository.\n\n"
                    "Please make sure:\n"
                    "1. The repository was indexed "
                    "successfully.\n"
                    "2. The filename/path is correct.\n"
                    "3. The file exists in the repository."
                ),

                "sources": [],

            }

        return {

            "target": target,

            "documentation": (
                "No indexed repository content "
                "was found for this request. Please "
                "index the repository first, or try "
                "rephrasing your request."
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
    # PROJECT PROMPT
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

Never turn a README claim into an implementation
fact.
"""


    # ========================================================
    # TOPIC PROMPT
    # ========================================================

    elif retrieval_mode == "topic":

        instructions = f"""
You are documenting a SPECIFIC TOPIC requested
by the user:

{target_title}

You have been given README/documentation
evidence (if available) and source-code evidence
relevant to this topic.

Stay focused specifically on: {target_title}

Do NOT describe the entire project in general.
Only cover what is relevant to this topic.

Separate:

## Documentation Claims

What the README/documentation says about this
topic, if anything.

## Implementation Evidence

What the actual source code shows about this
topic, with file names and line ranges.

## Implementation Gaps

If insufficient evidence was retrieved to fully
cover this topic, explicitly say so instead of
guessing.

Never invent frameworks, libraries, files, or
functionality not present in the supplied
evidence.
"""


    # ========================================================
    # SPECIFIC FILE PROMPT
    # ========================================================

    else:

        instructions = f"""
You are documenting ONE SPECIFIC FILE.

REQUESTED FILE:

{target}

The repository evidence supplied below should
contain only chunks belonging to this requested
file.

IMPORTANT:

- Explain ONLY {target}.
- Do NOT explain another file.
- Do NOT substitute another file.
- Do NOT infer implementation from unrelated files.
- Use the actual file name and line ranges.
- If the supplied evidence is insufficient,
  explicitly say what cannot be determined.
- Do not invent functionality.

Explain:

1. What the file does
2. Important functions
3. Classes
4. Inputs
5. Outputs
6. Dependencies
7. Control flow
8. Error handling
9. Security considerations
10. Usage

Use ONLY the supplied implementation evidence.
"""


    # ========================================================
    # FINAL PROMPT
    # ========================================================

    prompt = f"""
You are a Senior Software Engineer and
Technical Documentation Specialist.

Your job is to create accurate developer
documentation for CodebaseIQ.

TARGET:

{target_title}

{instructions}

IMPORTANT OUTPUT RULES:

- Return ONLY the final documentation.
- Do NOT include <think> tags.
- Do NOT reveal internal reasoning.
- Do NOT describe your thinking process.
- Start directly with "# Overview".

IMPORTANT FACTUAL RULES:

- Use ONLY the supplied repository content.
- Do not invent files.
- Do not invent APIs.
- Do not invent classes.
- Do not invent functions.
- Do not invent behavior.
- Mention file names and line ranges.
- Be technically precise.
- Do not use outside knowledge to fill missing
  implementation details.

REPOSITORY CONTENT:

{context}

Generate documentation using this structure:

# Overview

Explain the purpose of the requested target.

# Documentation Claims

Explain functionality described by documentation,
if such documentation was supplied.

If none was supplied, explicitly say so.

# Implementation Evidence

Explain what the actual source code implements.

# Architecture

Describe the architecture supported by the
supplied source code.

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

Explain the actual execution flow.

# Dependencies

List libraries, frameworks and modules visible
in the supplied code.

# Error Handling

Describe actual error handling.

If none is present, say so.

# Security Considerations

Describe actual security mechanisms or
security-relevant code.

Do NOT invent vulnerabilities.

# Implementation Gaps

List functionality that cannot be verified from
the supplied implementation.

# Usage Example

Provide a usage example only when supported
by the code.

# Summary

Give a concise and accurate summary.

Remember:

DOCUMENTATION CLAIM != IMPLEMENTATION FACT.
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

                temperature=0.2,

                max_tokens=3000,

            )
        )


        # Get raw model response

        raw_documentation = (
            completion
            .choices[0]
            .message
            .content
        )


        # Remove <think> reasoning

        documentation = _clean_llm_response(
            raw_documentation
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

        "target": target,

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

        repo_url=(
            "https://github.com/"
            "Tarandeepkaur88/ReZniX"
        ),

        target="tech stack of frontend and backend",

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