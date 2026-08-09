# CodebaseIQ

CodebaseIQ indexes a Git repository and finds relevant source-code chunks for a natural-language question. It currently provides a FastAPI backend; a frontend can be added on top of the two API endpoints.

## What does this project do

1. Clones a public Git repository into a temporary directory.
2. Finds supported source and documentation files.
3. Chunks Python by top-level function/class, falling back to overlapping lines.
4. Creates local sentence-transformer embeddings and persists them in ChromaDB.
5. Retrieves the closest chunks for a question.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn backend.main:app --reload
```

The first index/query downloads the embedding model. Chroma data is stored in `.data/chroma` and is intentionally excluded from Git.
Set `GROQ_API_KEY` in `.env` to use the Q&A and code-review endpoints.

## API

Index a repository:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/index -ContentType 'application/json' -Body '{"repo_url":"https://github.com/octocat/Hello-World"}'
```

Search an indexed repository:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/query -ContentType 'application/json' -Body '{"repo_url":"https://github.com/octocat/Hello-World","question":"Where is the main logic?","limit":5}'
```

Analyze likely bugs and risks in retrieved code:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/analyze -ContentType 'application/json' -Body '{"repo_url":"https://github.com/octocat/Hello-World","question":"Find security bugs and error handling problems","limit":8}'
```

Run automated tests with `pytest`.
