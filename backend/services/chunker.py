import os

# Which file extensions we consider "code" worth chunking
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb",
    ".cpp", ".c", ".h", ".cs", ".php", ".md", ".txt"
}

def get_code_files(repo_path: str) -> list[str]:
    """
    Walks through the repo folder and returns paths to all code files,
    skipping .git, node_modules, venv, etc.
    """
    skip_dirs = {".git", "node_modules", "venv", "__pycache__", ".venv"}
    code_files = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in CODE_EXTENSIONS:
                code_files.append(os.path.join(root, f))

    return code_files


def chunk_file(file_path: str, chunk_size: int = 40, overlap: int = 5) -> list[dict]:
    """
    Splits a single file into overlapping chunks of `chunk_size` lines.
    Overlap helps avoid cutting a function/thought in half between chunks.
    Returns a list of dicts: {file, start_line, end_line, text}
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Skipping {file_path}: {e}")
        return []

    chunks = []
    i = 0
    while i < len(lines):
        chunk_lines = lines[i : i + chunk_size]
        text = "".join(chunk_lines).strip()
        if text:  # skip empty chunks
            chunks.append({
                "file": file_path,
                "start_line": i + 1,
                "end_line": min(i + chunk_size, len(lines)),
                "text": text
            })
        i += chunk_size - overlap  # move forward, but overlap a bit

    return chunks


def chunk_repo(repo_path: str) -> list[dict]:
    """
    Runs chunk_file on every code file in the repo.
    Returns one big list of chunks across the whole repo.
    """
    all_chunks = []
    code_files = get_code_files(repo_path)
    print(f"Found {len(code_files)} code files.")

    for file_path in code_files:
        chunks = chunk_file(file_path)
        all_chunks.extend(chunks)

    print(f"Created {len(all_chunks)} total chunks.")
    return all_chunks


if __name__ == "__main__":
    # test on the repo we cloned in step 2
    chunks = chunk_repo("cloned_repo")

    print("\nFirst 2 chunks preview:")
    for c in chunks[:2]:
        print(f"--- {c['file']} (lines {c['start_line']}-{c['end_line']}) ---")
        print(c["text"])
        print()
