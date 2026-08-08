"""Semantic and file-specific retrieval for CodebaseIQ."""

import chromadb

from backend.services.embeddings import embed_texts
from backend.services.indexer import collection_name
from backend.services.repo_reader import normalize_repo_url


class RepositorySearch:

    def __init__(
        self,
        persist_directory: str = ".data/chroma"
    ) -> None:

        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

    # =========================================================
    # NORMAL SEMANTIC SEARCH
    # Used by normal Q&A
    # =========================================================

    def query(
        self,
        repo_url: str,
        question: str,
        limit: int = 5
    ) -> list[dict]:

        repo_url = normalize_repo_url(repo_url)

        collection = self.client.get_collection(
            name=collection_name(repo_url),
            embedding_function=None
        )

        results = collection.query(
            query_embeddings=embed_texts([question]),
            n_results=limit,
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        output = []

        if not results.get("documents"):
            return output

        for document, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):

            output.append({
                "text": document,
                "metadata": metadata,
                "distance": distance
            })

        return output

    # =========================================================
    # FILE-SPECIFIC SEARCH
    # Used when user asks about a particular file
    # =========================================================

    def get_file_chunks(
        self,
        repo_url: str,
        file_name: str
    ) -> list[dict]:

        repo_url = normalize_repo_url(repo_url)

        collection = self.client.get_collection(
            name=collection_name(repo_url),
            embedding_function=None
        )

        # First try exact path
        results = collection.get(
            where={
                "file": file_name
            },
            include=[
                "documents",
                "metadatas"
            ]
        )

        documents = results.get(
            "documents",
            []
        )

        metadatas = results.get(
            "metadatas",
            []
        )

        # If exact path didn't work, try filename matching
        if not documents:

            all_results = collection.get(
                include=[
                    "documents",
                    "metadatas"
                ]
            )

            for document, metadata in zip(
                all_results.get("documents", []),
                all_results.get("metadatas", [])
            ):

                stored_file = metadata.get(
                    "file",
                    ""
                )

                if (
                    stored_file == file_name
                    or stored_file.endswith(
                        "/" + file_name
                    )
                    or stored_file.endswith(
                        "\\" + file_name
                    )
                ):

                    documents.append(
                        document
                    )

                    metadatas.append(
                        metadata
                    )

        output = []

        for document, metadata in zip(
            documents,
            metadatas
        ):

            output.append({
                "text": document,
                "metadata": metadata
            })

        # Keep chunks in source-code order
        output.sort(
            key=lambda x: (
                x["metadata"].get(
                    "start_line",
                    0
                )
            )
        )

        print(
            f"File search: '{file_name}' "
            f"→ {len(output)} chunks"
        )

        return output

    # =========================================================
    # ALL SOURCE CODE
    # Used by Bug Finder
    # =========================================================

    def get_all_source_chunks(
        self,
        repo_url: str,
        batch_size: int = 100
    ) -> list[dict]:

        repo_url = normalize_repo_url(repo_url)

        collection = self.client.get_collection(
            name=collection_name(repo_url),
            embedding_function=None
        )

        all_chunks = []

        offset = 0

        while True:

            results = collection.get(
                where={
                    "source": "code"
                },
                limit=batch_size,
                offset=offset,
                include=[
                    "documents",
                    "metadatas"
                ]
            )

            documents = results.get(
                "documents",
                []
            )

            metadatas = results.get(
                "metadatas",
                []
            )

            if not documents:
                break

            for document, metadata in zip(
                documents,
                metadatas
            ):

                all_chunks.append({
                    "text": document,
                    "metadata": metadata
                })

            offset += len(documents)

            if len(documents) < batch_size:
                break

        print(
            f"Loaded {len(all_chunks)} "
            f"source-code chunks."
        )

        return all_chunks