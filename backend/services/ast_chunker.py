import ast
import os


def chunk_python_file(file_path: str) -> list[dict]:
    """
    Parses a Python file using AST and extracts each function and class
    as its own chunk, respecting code boundaries (never cuts mid-function).
    Falls back to returning nothing if the file has a syntax error
    (caller should then use line-based chunking instead).
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        print(f"Could not read {file_path}: {e}")
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}, skipping AST parse: {e}")
        return []

    source_lines = source.splitlines()
    chunks = []

    # Avoid returning methods and nested functions separately: their text is
    # already included inside the enclosing class/function chunk.
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)

            # Grab the actual source text for this function/class
            text = "\n".join(source_lines[start_line - 1 : end_line]).strip()

            if text:
                chunks.append({
                    "file": file_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "type": type(node).__name__,  # e.g. "FunctionDef" or "ClassDef"
                    "name": node.name,
                    "text": text
                })

    return chunks


if __name__ == "__main__":
    # quick test: run it on THIS file itself
    chunks = chunk_python_file("services/ast_chunker.py")

    print(f"Found {len(chunks)} functions/classes.\n")
    for c in chunks:
        print(f"--- {c['type']} '{c['name']}' (lines {c['start_line']}-{c['end_line']}) ---")
        print(c["text"])
        print()
