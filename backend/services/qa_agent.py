import os
from dotenv import load_dotenv
from groq import Groq

from backend.services.search import RepositorySearch

# Load environment variables
load_dotenv()

def answer_question(repo_url: str, question: str, limit: int = 5) -> dict:
    """
    Agent 2 — Q&A Agent.
    1. Retrieves relevant code chunks.
    2. Sends only those chunks to the LLM.
    3. Returns the grounded answer with sources.
    """

    # Step 1: Retrieve relevant chunks
    matches = RepositorySearch().query(repo_url, question, limit)

    if not matches:
        return {
            "question": question,
            "answer": "I couldn't find any relevant code for this question. Try indexing the repository first.",
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
You are an expert software engineer.

Answer the user's question ONLY using the provided code snippets.

Rules:
- Do NOT make up information.
- If the answer cannot be determined from the snippets, say so.
- Mention relevant file names whenever possible.
- Keep the answer concise and accurate.

CODE SNIPPETS:
{context}

QUESTION:
{question}
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
            max_tokens=512,
        )

        answer = completion.choices[0].message.content

    except Exception as e:
        return {
            "question": question,
            "answer": f"Error generating answer: {str(e)}",
            "sources": []
        }

    # Step 5: Return answer
    return {
        "question": question,
        "answer": answer,
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
    result = answer_question(
        repo_url="https://github.com/Tarandeepkaur88/ReZniX",
        question="What does this project do?"
    )

    print("\n========== ANSWER ==========\n")
    print(result["answer"])

    print("\n========== SOURCES ==========\n")
    for source in result["sources"]:
        print(source)
