import os
from dotenv import load_dotenv
from groq import Groq
from backend.services.search import RepositorySearch

load_dotenv()


def generate_docs(repo_url: str, target: str = None, limit: int = 8) -> dict:
    """
    Agent 4 — Documentation Generator.

    Workflow:
    1. Retrieve the most relevant code snippets from ChromaDB.
    2. Build a context using those snippets.
    3. Ask Groq to generate professional developer documentation.
    4. Return the documentation along with source citations.
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
            f"(Lines {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')})"
        )

        context_blocks.append(
            f"{file_info}\n{m.get('text', '')}"
        )

    context = "\n\n---\n\n".join(context_blocks)

    # Step 3: Prompt
    prompt = f"""
You are a Senior Software Engineer and Technical Documentation Specialist.

Your task is to generate professional developer documentation for a codebase.

IMPORTANT RULES:
- Use ONLY the provided code snippets.
- Do NOT invent classes, functions, APIs, or features.
- If some information is unavailable, clearly state that it is not present in the retrieved code.
- Write clean Markdown.
- Mention file names whenever relevant.
- Explain the code so another developer can quickly understand it.

Target Module:
{target if target else "Entire Project"}

Retrieved Code:
{context}

Generate documentation using this exact structure:

# Overview
Explain the overall purpose of this module.

# Architecture
Describe the important components and how they interact.

# Key Components
For every important function or class include:
- Name
- File
- Purpose
- Inputs
- Outputs
- Important implementation details

# Workflow
Explain the execution flow step-by-step.

# Dependencies
Mention important libraries, frameworks, and modules used.

# Error Handling
Explain how errors or exceptions are handled.

# Security Considerations
Mention authentication, authorization, password hashing, sessions, validation, SQL queries, or any security mechanisms if present.

# Usage Example
Provide a short example of how a developer would use this module.

# Summary
Provide a concise summary.

Only document information supported by the retrieved code.
"""

    # Step 4: Generate documentation
    try:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        client = Groq(api_key=api_key)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=2048,
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
        target="authentication module"
    )

    print("\n========== DOCUMENTATION ==========\n")
    print(result["documentation"])

    print("\n========== SOURCES ==========\n")

    for source in result["sources"]:
        print(source)