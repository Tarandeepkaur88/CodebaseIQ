import os
from dotenv import load_dotenv
from groq import Groq
from backend.services.search import RepositorySearch

load_dotenv()


def generate_docs(repo_url: str, target: str = None, limit: int = 8) -> dict:
    """
    Agent 4 — Docs Writer.
    1. Retrieves relevant code chunks (general overview, or a specific focus area).
    2. Sends only those chunks to the LLM.
    3. Returns generated documentation with sources.
    """
    query = target if target else "overview of the main functionality of this project"

    # Step 1: Retrieve relevant chunks
    matches = RepositorySearch().query(repo_url, query, limit)
    if not matches:
        return {
            "target": target,
            "documentation": "No indexed code found for this repository. Try indexing it first.",
            "sources": []
        }

    # Step 2: Build context
    context_blocks = []
    for m in matches:
        metadata = m.get("metadata", {})
        file_info = (
            f"File: {metadata.get('file', 'unknown')} "
            f"(lines {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')})"
        )
        context_blocks.append(
            f"{file_info}\n{m.get('text', '')}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    # Step 3: Prompt
    prompt = f"""
You are a technical writer creating documentation for a codebase.
Use ONLY the provided code snippets below.
Rules:
- Do NOT make up information not present in the snippets.
- Write clear, well-structured documentation using Markdown headings.
- Explain the purpose of the code, key functions/classes, and how it fits into the project.
- Mention relevant file names whenever possible.

CODE SNIPPETS:
{context}

FOCUS AREA (if specified): {target if target else "General project overview"}
"""

    # Step 4: Call Groq
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        completion = Groq(api_key=api_key).chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        documentation = completion.choices[0].message.content
    except Exception as e:
        return {
            "target": target,
            "documentation": f"Error generating documentation: {str(e)}",
            "sources": []
        }

    # Step 5: Return result
    return {
        "target": target,
        "documentation": documentation,
        "sources": [
            {
                "file": m.get("metadata", {}).get("file"),
                "start_line": m.get("metadata", {}).get("start_line"),
                "end_line": m.get("metadata", {}).get("end_line"),
            }
            for m in matches
        ]
    }


if __name__ == "__main__":
    result = generate_docs(
        repo_url="https://github.com/Tarandeepkaur88/ReZniX",
        target="the database functions"
    )
    print("\n========== DOCUMENTATION ==========\n")
    print(result["documentation"])
    print("\n========== SOURCES ==========\n")
    for source in result["sources"]:
        print(source)