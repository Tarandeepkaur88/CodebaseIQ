"""Semantic retrieval over indexed repositories."""

import chromadb

from backend.services.embeddings import embed_texts
from backend.services.indexer import collection_name
from backend.services.repo_reader import normalize_repo_url


class RepositorySearch:
    def __init__(self, persist_directory: str = ".data/chroma") -> None:
        self.client = chromadb.PersistentClient(path=persist_directory)

    def query(self, repo_url: str, question: str, limit: int = 5) -> list[dict]:
        repo_url = normalize_repo_url(repo_url)
        collection = self.client.get_collection(name=collection_name(repo_url), embedding_function=None)
        results = collection.query(query_embeddings=embed_texts([question]), n_results=limit, include=["documents", "metadatas", "distances"])
        return [
            {"text": document, "metadata": metadata, "distance": distance}
            for document, metadata, distance in zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
        ]
