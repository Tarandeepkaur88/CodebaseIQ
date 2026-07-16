"""Retrieval-augmented code review agent."""

import os

from dotenv import load_dotenv
from groq import Groq

from backend.services.search import RepositorySearch


load_dotenv()


def _sources(matches: list[dict]) -> list[dict]:
    """Return de-duplicated source references for retrieved chunks."""
    seen: set[tuple[object, object, object]] = set()
    sources: list[dict] = []
    for match in matches:
        metadata = match.get("metadata", {})
        source = {
            "file": metadata.get("file"),
            "start_line": metadata.get("start_line"),
            "end_line": metadata.get("end_line"),
        }
        key = (source["file"], source["start_line"], source["end_line"])
        if key not in seen:
            seen.add(key)
            sources.append(source)
    return sources


def analyze_code(repo_url: str, question: str = "Review the code for issues.", limit: int = 8) -> dict:
    """Find likely bugs, security risks, and maintainability issues in relevant code."""
    matches = RepositorySearch().query(repo_url, question, limit)
    if not matches:
        return {
            "question": question,
            "analysis": "I couldn't find relevant code to review. Index the repository first.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(
        "File: {file} (lines {start}-{end})\n{code}".format(
            file=match.get("metadata", {}).get("file", "unknown"),
            start=match.get("metadata", {}).get("start_line", "?"),
            end=match.get("metadata", {}).get("end_line", "?"),
            code=match.get("text", ""),
        )
        for match in matches
    )
    prompt = f"""
You are a precise senior code reviewer. Review ONLY the supplied snippets in response
to the user's request. Identify concrete bugs, security vulnerabilities, performance
problems, and harmful practices only when supported by the code.

For every finding, give severity (critical/high/medium/low), file and line range,
the evidence, and a concise fix. Do not invent missing context. If there are no
supported findings, say so plainly.

CODE SNIPPETS:
{context}

REVIEW REQUEST:
{question}
"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        completion = Groq(api_key=api_key).chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=900,
        )
        analysis = completion.choices[0].message.content
    except Exception as exc:
        return {
            "question": question,
            "analysis": f"Error generating code analysis: {exc}",
            "sources": _sources(matches),
        }

    return {"question": question, "analysis": analysis, "sources": _sources(matches)}
