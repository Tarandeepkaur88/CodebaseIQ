# CodebaseIQ

CodebaseIQ is an AI-powered repository analysis platform that helps users understand unfamiliar GitHub codebases through natural-language interaction.

Instead of manually searching through files, users can index a repository and ask questions about its architecture, implementation, technologies, and functionality. The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant repository content before generating a response.

CodebaseIQ also includes an agentic workflow built with LangGraph. A router analyzes the user's request and sends it to one of three specialized agents:

- Repository Q&A Agent
- Bug Finder Agent
- Documentation Agent

Each agent works with repository context retrieved from the vector database and returns responses grounded in the indexed codebase.

---

## Project Demo

### Authentication

Users can sign up and sign in using Supabase Authentication.

<p align="center">
  <img src="./screenshots/login.png" alt="CodebaseIQ Login Page" width="850">
</p>

---

### Repository Workspace

After authentication, users can paste a GitHub repository URL and index it. Indexed repositories appear in the sidebar and can be selected for further interaction.

<p align="center">
  <img src="./screenshots/dashboard.png" alt="CodebaseIQ Repository Dashboard" width="1000">
</p>

The interface also provides example prompts for the three main capabilities:

- Ask questions about the repository
- Analyze the repository for bugs or security issues
- Generate documentation

---

### Repository Q&A

The Q&A Agent answers questions about the selected repository using retrieved repository content.

For example:

> What tech stack is used in frontend and backend?

The system retrieves relevant documentation and implementation files before generating the response.

<p align="center">
  <img src="./screenshots/qa-agent.png" alt="CodebaseIQ Q&A Agent" width="1000">
</p>

The response is accompanied by source references showing the files and line ranges used as evidence.

---

### Documentation Generation

The Documentation Agent generates structured explanations based on the actual repository content.

For example:

> Generate documentation for the main functions

<p align="center">
  <img src="./screenshots/docs-agent.png" alt="CodebaseIQ Documentation Agent" width="1000">
</p>

The generated documentation explains the relevant functionality and includes implementation evidence from repository files.

---

### Bug Analysis

The Bug Finder Agent analyzes repository code for potential bugs, security concerns, and code-quality issues.

For example:

> Are there any bugs or security issues?

<p align="center">
  <img src="./screenshots/bug-agent.png" alt="CodebaseIQ Bug Finder Agent" width="1000">
</p>

The analysis is based on repository code retrieved for the request and returns findings together with file and line references.

---

# Overview

Understanding an unfamiliar codebase can be time-consuming. Developers often need to inspect multiple files, trace dependencies, understand data flow, and compare documentation with implementation.

CodebaseIQ provides a single interface for interacting with a repository using natural language.

The general workflow is:

```text
GitHub Repository
        │
        ▼
Repository Indexing
        │
        ▼
Code and Documentation Chunking
        │
        ▼
Sentence Transformer Embeddings
        │
        ▼
ChromaDB Vector Store
        │
        ▼
User Request
        │
        ▼
LangGraph Router
        │
        ├───────────────┬────────────────┐
        ▼               ▼                ▼
     Q&A Agent      Bug Finder      Docs Agent
        │               │                │
        └───────────────┴────────────────┘
                        │
                        ▼
                 RAG Retrieval
                        │
                        ▼
                  Groq LLM
                        │
                        ▼
          Grounded Response + Sources
Key Features
Index public GitHub repositories
AST-based chunking for Python code
Line-based chunking for other supported files
Semantic repository search
Sentence Transformer embeddings
ChromaDB vector storage
Retrieval-Augmented Generation
LangGraph-based agent routing
Repository Q&A
Bug and code-quality analysis
Documentation generation
File and line-range source references
Supabase Authentication
User-specific repository and chat history
Row-Level Security for database access
System Architecture

CodebaseIQ consists of four main parts:

┌──────────────────────────────────────────────┐
│                  React Frontend              │
│                                              │
│  Authentication │ Repository │ Chat Interface│
└───────────────────────┬──────────────────────┘
                        │
                        │ REST API
                        ▼
┌──────────────────────────────────────────────┐
│                 FastAPI Backend              │
│                                              │
│  /index                                    │
│  /query                                    │
│  /analyze                                  │
│  /generate-docs                            │
│  /agent                                    │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────┐
│              LangGraph Orchestrator          │
│                                              │
│               Intent Router                  │
└───────────────┬───────────────┬──────────────┘
                │               │
        ┌───────▼───────┐ ┌────▼────────┐
        │   Q&A Agent   │ │ Bug Finder  │
        └───────┬───────┘ └────┬────────┘
                │              │
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │ Docs Agent   │
                └──────┬───────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                 RAG Pipeline                 │
│                                              │
│  Repository Search → Relevant Code Chunks    │
│  → Context → LLM Response                    │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
                 ┌────────────┐
                 │ ChromaDB   │
                 └────────────┘
How Repository Indexing Works

The indexing pipeline prepares repository content for semantic search.

Step 1: User provides a GitHub repository URL

Example:

https://github.com/username/project

The request is sent to the backend:

POST /index

Example request body:

{
  "repo_url": "https://github.com/username/project"
}
Step 2: Repository is cloned

The backend retrieves the repository into a temporary working directory.

The repository files are then scanned to identify supported source and documentation files.

Step 3: Files are chunked

Different types of files require different chunking strategies.

Python files

Python files are processed using AST-based chunking where applicable.

This allows meaningful code structures such as functions and classes to be preserved as chunks rather than splitting code randomly.

Example:

def calculate_score(data):
    ...

The chunk can store metadata such as:

File: backend/services/example.py
Start Line: 10
End Line: 35
Other files

Documentation and other supported text-based files are split into smaller line-based chunks.

This helps preserve source locations that can later be shown to the user.

Step 4: Embeddings are created

Each chunk is converted into a vector representation using a Sentence Transformer model.

The project uses:

all-MiniLM-L6-v2

Conceptually:

Repository Code
       │
       ▼
Code Chunk
       │
       ▼
Sentence Transformer
       │
       ▼
Vector Embedding
Step 5: Chunks are stored in ChromaDB

The embeddings and their metadata are stored in ChromaDB.

Each stored chunk can include information such as:

Repository URL
File Name
Start Line
End Line
Chunk Content
Embedding

This makes it possible to perform semantic searches over the repository later.

Retrieval-Augmented Generation

When a user asks a question, CodebaseIQ does not simply send the entire repository to the language model.

Instead, it first searches for relevant repository content.

The retrieval flow is:

User Question
      │
      ▼
Convert Question into an Embedding
      │
      ▼
Semantic Search in ChromaDB
      │
      ▼
Retrieve Most Relevant Code Chunks
      │
      ▼
Build Context
      │
      ▼
Send Context + User Request to Agent
      │
      ▼
Generate Response
      │
      ▼
Return Sources

For example, if the user asks:

What technologies are used in this project?

The system searches the indexed repository for semantically relevant content.

Possible retrieved evidence might include:

README.md:1-40
README.md:36-75
backend/main.py:1-80
requirements.txt:1-30

The relevant context is then passed to the Q&A Agent.

This approach helps keep responses connected to the actual repository content.

Agentic AI Workflow

CodebaseIQ uses LangGraph to coordinate the specialized agents.

The workflow starts with a router.

                    User Message
                         │
                         ▼
                  LangGraph Router
                         │
             Intent Classification
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
         qa             bug            docs
          │              │              │
          ▼              ▼              ▼
      Q&A Agent      Bug Finder     Docs Agent
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                      Result

The router decides which specialized agent should handle the request.

Agent 1: Repository Q&A Agent

The Repository Q&A Agent is responsible for answering questions about the selected codebase.

Examples:

What does this project do?
How does authentication work?
What tech stack is used?
Explain the repository architecture.
Q&A Agent Workflow
User Question
      │
      ▼
LangGraph Router
      │
      ▼
Intent = "qa"
      │
      ▼
Repository Search
      │
      ▼
Retrieve Relevant Chunks
      │
      ▼
Build Grounded Context
      │
      ▼
Groq LLM
      │
      ▼
Answer + Source References
Evidence in the response

The Q&A Agent returns the repository sources used to generate the answer.

For example:

README.md:1-40
README.md:36-75
eval_full.py:83-110

This gives the user visibility into where the information came from.

Agent 2: Bug Finder Agent

The Bug Finder Agent analyzes the repository for potential implementation problems.

It can handle requests such as:

Are there any bugs or security issues?
Review this codebase for problems.
Are there any performance issues?
Check the project for vulnerabilities.
Bug Finder Workflow
User Request
      │
      ▼
LangGraph Router
      │
      ▼
Intent = "bug"
      │
      ▼
Bug Finder Agent
      │
      ▼
Retrieve Relevant Repository Code
      │
      ▼
Analyze Code
      │
      ▼
Generate Findings
      │
      ▼
Return Evidence

The agent analyzes the retrieved repository context for issues such as:

Potential bugs
Security concerns
Error handling problems
Code-quality issues
Implementation inconsistencies
Performance concerns where identifiable from the retrieved code

The result includes repository references where available.

Example:

eval_full.py:74-81
eval_full.py:83-110
Agent 3: Documentation Agent

The Documentation Agent generates structured technical documentation based on repository content.

Examples:

Generate documentation for the main functions.
Document the database functions.
Explain the architecture.
Create documentation for the backend.
Documentation Agent Workflow
User Request
      │
      ▼
LangGraph Router
      │
      ▼
Intent = "docs"
      │
      ▼
Documentation Agent
      │
      ▼
Retrieve Relevant Repository Files
      │
      ▼
Collect Implementation Evidence
      │
      ▼
Generate Structured Documentation
      │
      ▼
Return Documentation + Sources

The Documentation Agent can generate sections such as:

Overview
Main functionality
Architecture
Implementation details
Data flow
Important functions
Technology usage
Source evidence

The goal is to generate documentation based on retrieved repository content rather than producing a generic project description.

LangGraph Orchestration

The LangGraph workflow connects the router to the three specialized agents.

The conceptual structure is:

START
  │
  ▼
Router
  │
  ├──── qa ────► Q&A Agent ────► END
  │
  ├──── bug ───► Bug Finder ───► END
  │
  └──── docs ──► Docs Agent ───► END

The router classifies the request into one of three categories:

Intent	Selected Agent	Purpose
qa	Repository Q&A Agent	Answers questions about the codebase
bug	Bug Finder Agent	Analyzes bugs, security, and code issues
docs	Documentation Agent	Generates technical documentation

This provides a clear separation between the responsibilities of each agent.

Example Agent Routing
Request
What does this project do?
Router Decision
qa
Selected Agent
Repository Q&A Agent
Workflow
Question
   ↓
Retrieve Relevant Repository Chunks
   ↓
Build Context
   ↓
Generate Answer
   ↓
Return Sources
Request
Are there any bugs or security issues?
Router Decision
bug
Selected Agent
Bug Finder Agent
Workflow
Request
   ↓
Retrieve Relevant Code
   ↓
Analyze Retrieved Code
   ↓
Identify Potential Issues
   ↓
Return Findings + Sources
Request
Generate documentation for the main functions.
Router Decision
docs
Selected Agent
Documentation Agent
Workflow
Request
   ↓
Retrieve Relevant Functions
   ↓
Collect Implementation Context
   ↓
Generate Structured Documentation
   ↓
Return Sources
Technology Stack
Frontend
React
Vite
JavaScript
HTML
CSS
Backend
Python
FastAPI
Pydantic
AI and Agent Framework
LangGraph
Groq
Qwen
Retrieval and Vector Search
Sentence Transformers
all-MiniLM-L6-v2
ChromaDB
Authentication and Database
Supabase Authentication
Supabase PostgreSQL
Row-Level Security
Other
REST APIs
GitHub repositories
Environment variables
API Endpoints

The FastAPI backend exposes the following endpoints.

Method	Endpoint	Description
GET	/health	Checks whether the backend is running
POST	/index	Indexes a GitHub repository
POST	/query	Sends a direct repository question to the Q&A system
POST	/analyze	Performs repository bug analysis
POST	/generate-docs	Generates repository documentation
POST	/agent	Routes a natural-language request through LangGraph
/index

Indexes a GitHub repository.

Request
{
  "repo_url": "https://github.com/username/project"
}
Example Response
{
  "repository": "https://github.com/username/project",
  "collection": "repo_xxxxxxxxxxxxxxxx",
  "chunks_indexed": 9
}

The response confirms that the repository was indexed and reports the number of chunks created.

/query

Answers a question about an indexed repository.

Request
{
  "repo_url": "https://github.com/username/project",
  "question": "What does this project do?",
  "limit": 10
}

The backend retrieves relevant repository chunks and generates an answer from that context.

/analyze

Analyzes repository code for bugs and potential issues.

Request
{
  "repo_url": "https://github.com/username/project",
  "question": "Are there any bugs or security issues?"
}
/generate-docs

Generates documentation for a repository or a specific area of the repository.

Request
{
  "repo_url": "https://github.com/username/project",
  "target": "Generate documentation for the main functions",
  "limit": 10
}
/agent

This is the main agentic endpoint.

The request is first processed by the LangGraph router.

Request
{
  "repo_url": "https://github.com/username/project",
  "message": "Are there any bugs or security issues?"
}
Conceptual Response
{
  "intent": "bug",
  "agent": "Bug Finder Agent",
  "workflow": {
    "framework": "LangGraph",
    "router": "Intent Router",
    "selected_agent": "Bug Finder Agent",
    "status": "completed"
  },
  "result": {}
}
Authentication and User Data

CodebaseIQ uses Supabase for authentication and user data management.

The frontend initializes the Supabase client using environment variables:

import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;

const supabaseAnonKey =
  import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(
  supabaseUrl,
  supabaseAnonKey
);

The application uses Supabase Authentication to identify the current user.

Repository History

Indexed repositories can be associated with the authenticated user.

The repository data can include:

user_id
repo_url
chunks_count
created_at

Example frontend operation:

Authenticated User
       │
       ▼
Index Repository
       │
       ▼
Save Repository Metadata
       │
       ▼
Repository Appears in User History
Chat History

User messages and system responses can also be stored.

The chat history structure includes:

user_id
repo_url
role
message
intent
sources
created_at

This allows repository conversations to remain associated with the user and repository.

Security

Sensitive credentials are stored using environment variables.

The project uses separate environment variables for the backend and frontend.

Backend .env
GROQ_API_KEY=your_groq_api_key

SUPABASE_URL=your_supabase_url

SUPABASE_KEY=your_supabase_backend_key
Frontend .env
VITE_SUPABASE_URL=your_supabase_url

VITE_SUPABASE_ANON_KEY=your_supabase_publishable_key

VITE_API_URL=http://127.0.0.1:8000

Important: Never commit real API keys or secrets to a public GitHub repository.

Supabase Row-Level Security is used to support user-specific data access at the database layer.

Project Structure
CodebaseIQ/
│
├── backend/
│   │
│   ├── services/
│   │   ├── indexer.py
│   │   ├── qa_agent.py
│   │   ├── bug_agent.py
│   │   ├── docs_agent.py
│   │   ├── orchestrator.py
│   │   └── auth.py
│   │
│   └── main.py
│
├── frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   └── ...
│   │
│   └── ...
│
├── screenshots/
│   ├── login.png
│   ├── dashboard.png
│   ├── qa-agent.png
│   ├── docs-agent.png
│   └── bug-agent.png
│
├── requirements.txt
│
└── README.md
Running the Project Locally
1. Clone the repository
git clone <your-repository-url>
cd CodebaseIQ
Backend Setup
2. Create a virtual environment
python -m venv venv
3. Activate the environment
macOS / Linux
source backend/venv/bin/activate

Depending on where your virtual environment is created, the activation path may be:

source venv/bin/activate
4. Install dependencies
pip install -r requirements.txt
5. Configure environment variables

Create a .env file and add:

GROQ_API_KEY=your_groq_api_key

SUPABASE_URL=your_supabase_url

SUPABASE_KEY=your_supabase_key
6. Start the backend

From the project root:

uvicorn backend.main:app --reload

The backend should run at:

http://127.0.0.1:8000

FastAPI's interactive API documentation is available at:

http://127.0.0.1:8000/docs
Frontend Setup

Open another terminal and navigate to the frontend directory.

cd frontend

Install the dependencies:

npm install

Create a frontend .env file:

VITE_SUPABASE_URL=your_supabase_url

VITE_SUPABASE_ANON_KEY=your_supabase_publishable_key

VITE_API_URL=http://127.0.0.1:8000

Start the frontend:

npm run dev

The Vite development server will display the local application URL.

Testing the Backend

After starting the backend, open:

http://127.0.0.1:8000/docs

You can test the repository indexing endpoint.

Example:

{
  "repo_url": "https://github.com/Tarandeepkaur88/Insight-CXR"
}

A successful response can look like:

{
  "repository": "https://github.com/Tarandeepkaur88/Insight-CXR",
  "collection": "repo_533015ac83d313ee",
  "chunks_indexed": 9
}

Once indexed, the repository can be queried through the Q&A, bug analysis, documentation, or agent endpoints.

Example End-to-End Flow

A complete user interaction looks like this:

1. User signs in
        │
        ▼
2. User enters GitHub repository URL
        │
        ▼
3. Backend clones and indexes repository
        │
        ▼
4. Repository content is chunked
        │
        ▼
5. Embeddings are created
        │
        ▼
6. Embeddings are stored in ChromaDB
        │
        ▼
7. User asks a natural-language question
        │
        ▼
8. LangGraph Router classifies the request
        │
        ├── Q&A
        ├── Bug Analysis
        └── Documentation
        │
        ▼
9. Selected agent retrieves relevant context
        │
        ▼
10. Groq LLM generates a grounded response
        │
        ▼
11. Response and source references are displayed
Why RAG?

Sending an entire repository directly to a language model can be inefficient and may include irrelevant information.

CodebaseIQ uses retrieval to first identify relevant parts of the repository.

Instead of:

Entire Repository
        ↓
LLM

The workflow becomes:

User Request
        ↓
Semantic Search
        ↓
Relevant Repository Chunks
        ↓
LLM
        ↓
Grounded Response

This makes the context more focused on the user's request.

Why Multiple Agents?

Different repository tasks require different types of responses.

A question such as:

What does this function do?

is different from:

Are there any security issues?

which is also different from:

Generate documentation for this module.

CodebaseIQ separates these responsibilities into specialized agents.

                  User Request
                        │
                        ▼
                    Router
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
       Q&A             Bug            Docs
         │              │              │
         ▼              ▼              ▼
   Explanation      Analysis      Documentation

LangGraph manages this routing workflow.

Current Limitations

CodebaseIQ is currently designed as a repository analysis project and has some limitations.

Retrieval quality depends on the repository content that has been indexed.
Very large repositories may require additional indexing and storage optimization.
Bug analysis is based on retrieved code and should not be considered a replacement for a complete security audit.
Private repository support may require additional repository authentication.
The current system can be extended with more advanced multi-step agent workflows.
Repositories need to be indexed before they can be queried.
Future Improvements

Possible future improvements include:

Support for private GitHub repositories
Automatic repository re-indexing
GitHub webhook integration
Pull request analysis
More specialized agents
Multi-agent collaboration for complex requests
Streaming responses
Conversation memory
Repository architecture diagrams
Dependency visualization
Export generated documentation
Support for additional programming languages
More scalable vector storage
