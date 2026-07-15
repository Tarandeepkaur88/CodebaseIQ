"""Repository-to-vector-store indexing pipeline."""

import hashlib
import os
import tempfile
from pathlib import Path

import chromadb
from chromadb.errors import NotFoundError

from backend.services.ast_chunker import chunk_python_file
from backend.services.chunker import chunk_file, get_code_files
from backend.services.embeddings import embed_texts
from backend.services.repo_reader import clone_repo, normalize_repo_url


def collection_name(repo_url: str) -> str:
    """Produce a stable Chroma-safe collection name for one repository."""
    digest = hashlib.sha256(repo_url.encode("utf-8")).hexdigest()[:16]
    return f"repo_{digest}"


class RepositoryIndexer:
    def __init__(self, persist_directory: str = ".data/chroma") -> None:
        self.client = chromadb.PersistentClient(path=persist_directory)

    def _chunks_for_repo(self, repo_path: str) -> list[dict]:
        chunks: list[dict] = []
        for file_path in get_code_files(repo_path):
            file_chunks = chunk_python_file(file_path) if Path(file_path).suffix == ".py" else []
            # Syntax errors, empty modules, and non-Python files use line chunks.
            chunks.extend(file_chunks or chunk_file(file_path))
        return chunks

    def index_repository(self, repo_url: str) -> dict:
        repo_url = normalize_repo_url(repo_url)
        with tempfile.TemporaryDirectory(prefix="codebaseiq-") as temp_dir:
            repo_path = os.path.join(temp_dir, "repository")
            clone_repo(repo_url, repo_path)
            chunks = self._chunks_for_repo(repo_path)
            name = collection_name(repo_url)
            # A re-index must represent the current checkout, not a mixture
            # of current and previously deleted source files.
            try:
                self.client.delete_collection(name)
            except (NotFoundError, ValueError):
                pass
            collection = self.client.create_collection(name=name, embedding_function=None)
            if chunks:
                documents = [chunk["text"] for chunk in chunks]
                ids = [
                    hashlib.sha256(
                        f"{repo_url}:{chunk['file']}:{chunk['start_line']}:{chunk['end_line']}:{chunk['text']}".encode("utf-8")
                    ).hexdigest()
                    for chunk in chunks
                ]
                metadatas = [
                    {
                        "file": os.path.relpath(chunk["file"], repo_path).replace("\\", "/"),
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"],
                        "type": chunk.get("type", "line_chunk"),
                        "name": chunk.get("name", ""),
                    }
                    for chunk in chunks
                ]
                collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embed_texts(documents))
        return {"repository": repo_url, "collection": name, "chunks_indexed": len(chunks)}
