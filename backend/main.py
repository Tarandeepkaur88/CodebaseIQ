"""FastAPI application for indexing and searching Git repositories."""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.services.indexer import RepositoryIndexer
from backend.services.qa_agent import answer_question  # <-- NEW IMPORT
from backend.services.bug_agent import analyze_code
from backend.services.docs_agent import generate_docs

app = FastAPI(title="CodebaseIQ", version="0.1.0")
logger = logging.getLogger(__name__)


class IndexRequest(BaseModel):
    repo_url: str = Field(min_length=1, description="Git repository URL")


class QueryRequest(IndexRequest):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class AnalysisRequest(QueryRequest):
    limit: int = Field(default=8, ge=1, le=20)


class DocsRequest(IndexRequest):
    target: str | None = Field(default=None, description="Optional focus area, e.g. 'the database functions'")
    limit: int = Field(default=8, ge=1, le=20)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/index")
def index_repository(request: IndexRequest) -> dict:
    try:
        return RepositoryIndexer().index_repository(request.repo_url)
    except Exception as exc:
        logger.exception("Repository indexing failed for %s", request.repo_url)
        raise HTTPException(
            status_code=400,
            detail=f"Could not index repository: {exc}"
        ) from exc


@app.post("/query")
def query_repository(request: QueryRequest) -> dict:
    try:
        return answer_question(
            repo_url=request.repo_url,
            question=request.question,
            limit=request.limit,
        )
    except Exception as exc:
        logger.exception("Repository query failed for %s", request.repo_url)
        raise HTTPException(
            status_code=500,
            detail=f"Could not answer question: {exc}"
        ) from exc


@app.post("/analyze")
def analyze_repository(request: AnalysisRequest) -> dict:
    """Review retrieved repository code for likely issues."""
    try:
        return analyze_code(
            repo_url=request.repo_url,
            question=request.question,
            limit=request.limit,
        )
    except Exception as exc:
        logger.exception("Repository analysis failed for %s", request.repo_url)
        raise HTTPException(
            status_code=500,
            detail=f"Could not analyze repository: {exc}",
        ) from exc


@app.post("/generate-docs")
def generate_documentation(request: DocsRequest) -> dict:
    """Generate documentation for the repository, optionally focused on a target area."""
    try:
        return generate_docs(
            repo_url=request.repo_url,
            target=request.target,
            limit=request.limit,
        )
    except Exception as exc:
        logger.exception("Documentation generation failed for %s", request.repo_url)
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate documentation: {exc}",
        ) from exc