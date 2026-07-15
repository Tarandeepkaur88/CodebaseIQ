"""FastAPI application for indexing and searching Git repositories."""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.services.indexer import RepositoryIndexer
from backend.services.search import RepositorySearch

app = FastAPI(title="CodebaseIQ", version="0.1.0")
logger = logging.getLogger(__name__)


class IndexRequest(BaseModel):
    repo_url: str = Field(min_length=1, description="Git repository URL")


class QueryRequest(IndexRequest):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/index")
def index_repository(request: IndexRequest) -> dict:
    try:
        return RepositoryIndexer().index_repository(request.repo_url)
    except Exception as exc:
        logger.exception("Repository indexing failed for %s", request.repo_url)
        raise HTTPException(status_code=400, detail=f"Could not index repository: {exc}") from exc


@app.post("/query")
def query_repository(request: QueryRequest) -> dict:
    try:
        matches = RepositorySearch().query(request.repo_url, request.question, request.limit)
        return {"repository": request.repo_url, "matches": matches}
    except Exception as exc:
        logger.exception("Repository search failed for %s", request.repo_url)
        raise HTTPException(status_code=404, detail=f"Repository is not indexed or cannot be searched: {exc}") from exc
