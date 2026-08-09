import os


# ============================================================
# SOURCE CODE EXTENSIONS
# ============================================================

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",

    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",

    ".json",
    ".yaml",
    ".yml",
    ".xml",

    ".java",
    ".go",
    ".rb",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rs",
    ".sql",
}


# ============================================================
# DOCUMENTATION EXTENSIONS
# ============================================================

DOC_EXTENSIONS = {
    ".md",
    ".rst",
}


# ============================================================
# DIRECTORIES TO IGNORE
# ============================================================

SKIP_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
}


# ============================================================
# FIND SOURCE CODE FILES
# ============================================================

def get_code_files(
    repo_path: str
) -> list[str]:

    files_found = []

    for root, dirs, files in os.walk(repo_path):

        dirs[:] = [
            d
            for d in dirs
            if d not in SKIP_DIRS
        ]

        for file_name in files:

            extension = os.path.splitext(
                file_name
            )[1].lower()

            if extension in CODE_EXTENSIONS:

                files_found.append(
                    os.path.join(
                        root,
                        file_name
                    )
                )

    return files_found


# ============================================================
# FIND DOCUMENTATION FILES
# ============================================================

def get_documentation_files(
    repo_path: str
) -> list[str]:

    files_found = []

    for root, dirs, files in os.walk(repo_path):

        dirs[:] = [
            d
            for d in dirs
            if d not in SKIP_DIRS
        ]

        for file_name in files:

            extension = os.path.splitext(
                file_name
            )[1].lower()

            if extension in DOC_EXTENSIONS:

                files_found.append(
                    os.path.join(
                        root,
                        file_name
                    )
                )

    return files_found


# ============================================================
# CHUNK NORMAL FILE
# ============================================================

def chunk_file(
    file_path: str,
    chunk_size: int = 40,
    overlap: int = 5,
    chunk_type: str = "source_code"
) -> list[dict]:

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            lines = f.readlines()

    except Exception as e:

        print(
            f"Skipping {file_path}: {e}"
        )

        return []

    chunks = []

    i = 0

    while i < len(lines):

        chunk_lines = lines[
            i:i + chunk_size
        ]

        text = "".join(
            chunk_lines
        ).strip()

        if text:

            chunks.append({

                "file": file_path,

                "start_line": i + 1,

                "end_line": min(
                    i + chunk_size,
                    len(lines)
                ),

                "type": chunk_type,

                "name": "",

                "text": text,
            })

        i += (
            chunk_size - overlap
        )

    return chunks


# ============================================================
# CHUNK ENTIRE REPOSITORY
# ============================================================

def chunk_repo(
    repo_path: str
) -> list[dict]:

    all_chunks = []

    # -----------------------------
    # Source code
    # -----------------------------

    code_files = get_code_files(
        repo_path
    )

    print(
        f"Found {len(code_files)} source files."
    )

    for file_path in code_files:

        print(
            f"Reading source: {file_path}"
        )

        chunks = chunk_file(
            file_path,
            chunk_type="source_code"
        )

        all_chunks.extend(
            chunks
        )

    # -----------------------------
    # Documentation
    # -----------------------------

    documentation_files = (
        get_documentation_files(
            repo_path
        )
    )

    print(
        f"Found {len(documentation_files)} "
        f"documentation files."
    )

    for file_path in documentation_files:

        print(
            f"Reading documentation: {file_path}"
        )

        chunks = chunk_file(
            file_path,
            chunk_type="documentation"
        )

        all_chunks.extend(
            chunks
        )

    print(
        f"Created {len(all_chunks)} total chunks."
    )

    return all_chunks


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    chunks = chunk_repo(
        "cloned_repo"
    )

    print(
        "\nFirst 5 chunks:"
    )

    for chunk in chunks[:5]:

        print(
            f"\n--- {chunk['file']} "
            f"({chunk['start_line']}-"
            f"{chunk['end_line']}) ---"
        )

        print(
            f"TYPE: {chunk['type']}"
        )

        print(
            chunk["text"]
        )