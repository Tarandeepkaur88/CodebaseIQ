"""Repository-to-vector-store indexing pipeline."""

import hashlib
import os
import tempfile

import chromadb

from chromadb.errors import NotFoundError

from backend.services.ast_chunker import (
    chunk_python_file
)

from backend.services.chunker import (
    chunk_file,
    get_code_files,
    get_documentation_files
)

from backend.services.embeddings import (
    embed_texts
)

from backend.services.repo_reader import (
    clone_repo,
    normalize_repo_url
)


def collection_name(
    repo_url: str
) -> str:

    digest = hashlib.sha256(
        repo_url.encode("utf-8")
    ).hexdigest()[:16]

    return f"repo_{digest}"


class RepositoryIndexer:

    def __init__(
        self,
        persist_directory: str = ".data/chroma"
    ) -> None:

        self.client = (
            chromadb.PersistentClient(
                path=persist_directory
            )
        )

    # ========================================================
    # CREATE ALL CHUNKS
    # ========================================================

    def _chunks_for_repo(
        self,
        repo_path: str
    ) -> list[dict]:

        chunks = []

        # ----------------------------------------------------
        # SOURCE CODE
        # ----------------------------------------------------

        code_files = get_code_files(
            repo_path
        )

        print(
            f"\nFound {len(code_files)} "
            f"source files."
        )

        for file_path in code_files:

            print(
                f"Reading source: {file_path}"
            )

            file_chunks = []

            # Python → AST
            if file_path.lower().endswith(
                ".py"
            ):

                file_chunks = (
                    chunk_python_file(
                        file_path
                    )
                )

            # If AST fails, line chunks
            if not file_chunks:

                file_chunks = chunk_file(
                    file_path,
                    chunk_type="source_code"
                )

            # Make sure AST chunks are marked
            # as source code
            for chunk in file_chunks:

                chunk["type"] = (
                    chunk.get(
                        "type",
                        "source_code"
                    )
                )

                chunk["source"] = "code"

            chunks.extend(
                file_chunks
            )

        # ----------------------------------------------------
        # DOCUMENTATION
        # ----------------------------------------------------

        documentation_files = (
            get_documentation_files(
                repo_path
            )
        )

        print(
            f"\nFound {len(documentation_files)} "
            f"documentation files."
        )

        for file_path in documentation_files:

            print(
                f"Reading documentation: {file_path}"
            )

            file_chunks = chunk_file(
                file_path,
                chunk_type="documentation"
            )

            for chunk in file_chunks:

                chunk["type"] = (
                    "documentation"
                )

                chunk["source"] = (
                    "documentation"
                )

            chunks.extend(
                file_chunks
            )

        print(
            f"\nTotal chunks created: "
            f"{len(chunks)}"
        )

        return chunks

    # ========================================================
    # INDEX REPOSITORY
    # ========================================================

    def index_repository(
        self,
        repo_url: str
    ) -> dict:

        repo_url = normalize_repo_url(
            repo_url
        )

        print(
            f"\nIndexing repository:"
            f"\n{repo_url}"
        )

        with tempfile.TemporaryDirectory(
            prefix="codebaseiq-"
        ) as temp_dir:

            repo_path = os.path.join(
                temp_dir,
                "repository"
            )

            # ------------------------------------------------
            # Clone
            # ------------------------------------------------

            clone_repo(
                repo_url,
                repo_path
            )

            # ------------------------------------------------
            # Chunk
            # ------------------------------------------------

            chunks = (
                self._chunks_for_repo(
                    repo_path
                )
            )

            # ------------------------------------------------
            # Collection
            # ------------------------------------------------

            name = collection_name(
                repo_url
            )

            try:

                self.client.delete_collection(
                    name
                )

                print(
                    "Deleted old collection."
                )

            except (
                NotFoundError,
                ValueError
            ):

                pass

            collection = (
                self.client.create_collection(
                    name=name,
                    embedding_function=None
                )
            )

            # ------------------------------------------------
            # Store
            # ------------------------------------------------

            if chunks:

                documents = [
                    chunk["text"]
                    for chunk in chunks
                ]

                ids = []

                metadatas = []

                for chunk in chunks:

                    relative_file = (
                        os.path.relpath(
                            chunk["file"],
                            repo_path
                        )
                        .replace(
                            "\\",
                            "/"
                        )
                    )

                    chunk_id = hashlib.sha256(
                        (
                            f"{repo_url}:"
                            f"{relative_file}:"
                            f"{chunk['start_line']}:"
                            f"{chunk['end_line']}:"
                            f"{chunk['text']}"
                        ).encode(
                            "utf-8"
                        )
                    ).hexdigest()

                    ids.append(
                        chunk_id
                    )

                    metadatas.append({

                        "file": relative_file,

                        "start_line":
                            chunk[
                                "start_line"
                            ],

                        "end_line":
                            chunk[
                                "end_line"
                            ],

                        "type":
                            chunk.get(
                                "type",
                                "source_code"
                            ),

                        "name":
                            chunk.get(
                                "name",
                                ""
                            ),

                        "source":
                            chunk.get(
                                "source",
                                "code"
                            ),
                    })

                print(
                    "\nCreating embeddings..."
                )

                embeddings = embed_texts(
                    documents
                )

                collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings
                )

                print(
                    f"\nIndexed {len(chunks)} chunks."
                )

            else:

                print(
                    "\nWARNING: No files found."
                )

        return {

            "repository":
                repo_url,

            "collection":
                name,

            "chunks_indexed":
                len(chunks),
        }