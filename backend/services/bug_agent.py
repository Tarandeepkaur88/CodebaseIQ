"""Repository-wide Bug Finder agent."""

import os

from dotenv import load_dotenv
from groq import Groq

from backend.services.search import RepositorySearch


load_dotenv()


# =============================================================
# SOURCE HELPERS
# =============================================================

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


# =============================================================
# GROQ CLIENT
# =============================================================

def _get_client() -> Groq:

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    return Groq(
        api_key=api_key
    )


# =============================================================
# ANALYZE ONE BATCH
# =============================================================

def _analyze_batch(
    client: Groq,
    batch: list[dict],
    question: str,
    batch_number: int
) -> str:

    context_parts = []

    for match in batch:

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

        code = match.get(
            "text",
            ""
        )

        context_parts.append(
            f"""
FILE: {file_name}
LINES: {start_line}-{end_line}

SOURCE CODE:
{code}
"""
        )

    context = "\n\n-------------------------\n\n".join(
        context_parts
    )

    prompt = f"""
You are CodebaseIQ's Bug Finder.

You are reviewing batch {batch_number} of a repository-wide
code security and correctness scan.

Review ONLY the source code provided below.

USER REQUEST:
{question}

STRICT RULES:

1. Only report issues supported by concrete evidence
   in the supplied source code.

2. Do NOT invent code, behavior, files, or line numbers.

3. Do NOT report theoretical vulnerabilities without
   evidence of an actual dangerous data flow.

4. Do NOT classify normal programming operations as
   security vulnerabilities.

5. The following are NOT vulnerabilities by themselves:

   - alert()
   - console.log()
   - preventDefault()
   - addEventListener()
   - element.style.opacity
   - CSS animations
   - hardcoded animation durations
   - checking whether DOM elements exist
   - descriptive variable names
   - multiple DOMContentLoaded listeners

6. For XSS, there must be evidence that untrusted data
   reaches a dangerous HTML/DOM sink such as:

   - innerHTML
   - outerHTML
   - document.write()
   - unsafe HTML insertion

7. For SQL injection, there must be evidence that
   untrusted input is incorporated into a database query
   unsafely.

8. For command injection, there must be evidence that
   untrusted input reaches a shell/system command.

9. For path traversal, there must be evidence that
   attacker-controlled paths are used without appropriate
   validation.

10. For hardcoded secrets, only report them if the supplied
    code actually contains something that looks like a real
    secret, API key, password, token, or credential.

11. Missing defensive checks are NOT automatically
    vulnerabilities.

12. If something is merely a code-quality improvement,
    classify it as Code Quality rather than Security.

13. Accuracy is more important than finding something.

14. If no confirmed issue exists in this batch, return:

    NO_CONFIRMED_FINDINGS

15. Every finding must include:

    Severity
    Type
    File
    Lines
    Evidence
    Why it matters
    Fix

16. Use ONLY the file and line numbers provided above.

SOURCE CODE:

{context}
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.0,

        max_tokens=1500
    )

    return (
        completion
        .choices[0]
        .message
        .content
    )


# =============================================================
# FINAL FINDING AGGREGATION
# =============================================================

def _combine_findings(
    client: Groq,
    batch_results: list[str],
    question: str
) -> str:

    findings = "\n\n====================\n\n".join(
        batch_results
    )

    prompt = f"""
You are the final security reviewer for CodebaseIQ.

The repository was analyzed in multiple independent batches.

USER REQUEST:
{question}

Here are the findings produced by the batch reviewers:

{findings}

Your job is to produce one accurate final report.

STRICT RULES:

1. Do not invent findings.

2. Remove duplicate findings that refer to the
   same underlying issue.

3. Do not turn code-quality observations into
   security vulnerabilities.

4. Only report findings that have concrete evidence
   from the batch results.

5. If a batch says NO_CONFIRMED_FINDINGS, that means
   it found nothing confirmed.

6. Do not claim that a vulnerability exists merely
   because a defensive check is missing.

7. Do not claim that the entire repository is secure.
   Say "No confirmed vulnerabilities were found in
   the analyzed source code" when appropriate.

8. Preserve exact file names and line ranges.

9. Rank findings by severity.

10. If there are no confirmed findings, say:

    No confirmed bugs or security vulnerabilities
    were found in the analyzed source code.

    Then optionally provide code-quality observations.

OUTPUT:

# Code Review

## Confirmed Findings

For each confirmed issue:

### [SEVERITY] Title

- Type:
- File:
- Lines:

**Evidence:**
...

**Why it matters:**
...

**Fix:**
...

If there are no confirmed findings:

No confirmed bugs or security vulnerabilities were
found in the analyzed source code.

## Code Quality Observations

Only include genuine maintainability or reliability
observations here.
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.0,

        max_tokens=2000
    )

    return (
        completion
        .choices[0]
        .message
        .content
    )


# =============================================================
# MAIN BUG FINDER
# =============================================================

def analyze_code(
    repo_url: str,
    question: str = (
        "Find bugs and security vulnerabilities "
        "in this repository."
    ),
    batch_size: int = 15
) -> dict:

    try:

        search = RepositorySearch()

        # -----------------------------------------------------
        # Get ALL source-code chunks
        # -----------------------------------------------------

        chunks = search.get_all_source_chunks(
            repo_url
        )

        if not chunks:

            return {
                "question": question,

                "analysis": (
                    "No source-code chunks were found. "
                    "Please index the repository first."
                ),

                "sources": []
            }

        print(
            f"\nBug Finder: "
            f"{len(chunks)} source chunks found."
        )

        # -----------------------------------------------------
        # Create Groq client
        # -----------------------------------------------------

        client = _get_client()

        # -----------------------------------------------------
        # Analyze repository in batches
        # -----------------------------------------------------

        batch_results = []

        total_batches = (
            len(chunks) + batch_size - 1
        ) // batch_size

        for i in range(
            0,
            len(chunks),
            batch_size
        ):

            batch = chunks[
                i:i + batch_size
            ]

            batch_number = (
                i // batch_size
            ) + 1

            print(
                f"\nBug Finder: "
                f"Analyzing batch "
                f"{batch_number}/{total_batches}"
            )

            result = _analyze_batch(
                client=client,
                batch=batch,
                question=question,
                batch_number=batch_number
            )

            batch_results.append(
                result
            )

        # -----------------------------------------------------
        # Combine findings
        # -----------------------------------------------------

        print(
            "\nBug Finder: "
            "Combining findings..."
        )

        final_analysis = _combine_findings(
            client=client,
            batch_results=batch_results,
            question=question
        )

        # -----------------------------------------------------
        # Sources
        # -----------------------------------------------------

        sources = _sources(
            chunks
        )

        print(
            "\nBug Finder completed."
        )

        return {
            "question": question,
            "analysis": final_analysis,
            "sources": sources
        }

    except Exception as exc:

        return {
            "question": question,

            "analysis": (
                f"Error generating code analysis: {exc}"
            ),

            "sources": []
        }