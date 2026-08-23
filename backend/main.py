"""FastAPI application for indexing and searching Git repositories."""

import logging

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.services.indexer import RepositoryIndexer
from backend.services.qa_agent import answer_question
from backend.services.bug_agent import analyze_code
from backend.services.docs_agent import generate_docs
from backend.services.orchestrator import handle_request
from backend.services.auth import get_current_user


app = FastAPI(
    title="CodebaseIQ",
    version="0.1.0",
)


# ---------------- CORS ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logger = logging.getLogger(__name__)


# ---------------- REQUEST MODELS ----------------

class IndexRequest(BaseModel):
    repo_url: str = Field(
        min_length=1,
        description="Git repository URL",
    )


class QueryRequest(IndexRequest):
    question: str = Field(
        min_length=1,
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=20,
    )


class AnalysisRequest(QueryRequest):
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
    )


class DocsRequest(IndexRequest):
    target: str | None = Field(
        default=None,
        description="Optional focus area, e.g. 'the database functions'",
    )

    limit: int = Field(
        default=8,
        ge=1,
        le=20,
    )


class AgentRequest(IndexRequest):
    message: str = Field(
        min_length=1,
        description="Natural language request for the AI agent",
    )


# ---------------- HEALTH ----------------

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok"
    }


# ---------------- INDEX REPOSITORY ----------------
# TEMPORARILY REMOVED AUTHENTICATION
# This helps us check whether Supabase auth is causing the problem.

@app.post("/index")
def index_repository(request: IndexRequest) -> dict:
    try:
        logger.info(
            "Starting indexing for repository: %s",
            request.repo_url,
        )

        result = RepositoryIndexer().index_repository(
            request.repo_url
        )

        logger.info(
            "Successfully indexed repository: %s",
            request.repo_url,
        )

        return result

    except Exception as exc:
        logger.exception(
            "Repository indexing failed for %s",
            request.repo_url,
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ---------------- QUERY ----------------

@app.post("/query")
def query_repository(
    request: QueryRequest,
    user=Depends(get_current_user),
) -> dict:
    try:
        return answer_question(
            repo_url=request.repo_url,
            question=request.question,
            limit=request.limit,
        )

    except Exception as exc:
        logger.exception(
            "Repository query failed for %s",
            request.repo_url,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Could not answer question: {exc}",
        ) from exc


# ---------------- ANALYZE ----------------

@app.post("/analyze")
def analyze_repository(
    request: AnalysisRequest,
    user=Depends(get_current_user),
) -> dict:
    try:
        return analyze_code(
            repo_url=request.repo_url,
            question=request.question,
            limit=request.limit,
        )

    except Exception as exc:
        logger.exception(
            "Repository analysis failed for %s",
            request.repo_url,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Could not analyze repository: {exc}",
        ) from exc


# ---------------- GENERATE DOCS ----------------

@app.post("/generate-docs")
def generate_documentation(
    request: DocsRequest,
    user=Depends(get_current_user),
) -> dict:
    try:
        return generate_docs(
            repo_url=request.repo_url,
            target=request.target,
            limit=request.limit,
        )

    except Exception as exc:
        logger.exception(
            "Documentation generation failed for %s",
            request.repo_url,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Could not generate documentation: {exc}",
        ) from exc


# ---------------- SMART AGENT ----------------

@app.post("/agent")
def agent(
    request: AgentRequest,
    user=Depends(get_current_user),
) -> dict:
    """
    Smart AI endpoint.

    Uses the LangGraph orchestrator + Groq LLM to automatically
    determine whether the request should be handled by:
      - QA Agent
      - Bug Finder Agent
      - Documentation Agent
    """

    try:
        return handle_request(
            repo_url=request.repo_url,
            message=request.message,
        )

    except Exception as exc:
        logger.exception(
            "Agent routing failed for %s",
            request.repo_url,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Agent request failed: {exc}",
        ) from exc