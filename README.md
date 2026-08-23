# 🚀 CodebaseIQ

<div align="center">

### Understand any codebase, instantly.

An AI-powered codebase intelligence platform that allows developers to index GitHub repositories, ask questions about their code, detect potential bugs, and generate documentation using RAG and AI agents.

</div>

---

## 📌 Overview

Understanding an unfamiliar codebase can be time-consuming. **CodebaseIQ** simplifies this process by indexing a GitHub repository and enabling intelligent interaction with its source code.

The system retrieves relevant code context and routes requests to specialized AI agents for tasks such as:

* 💬 Codebase Q&A
* 🐛 Bug and security analysis
* 📄 Documentation generation
* 🔍 Semantic code search

---

## ✨ Features

### 🔐 Authentication

Users can securely sign in and access the CodebaseIQ platform.

<p align="center">
  <img src="assets/login.png" alt="CodebaseIQ Login" width="600"/>
</p>

---

### 📂 Repository Indexing

Paste a GitHub repository URL and index the repository for AI-powered analysis.

The indexed repositories are available from the sidebar, allowing users to select and interact with different codebases.

<p align="center">
  <img src="assets/codebase-home.png" alt="Repository Indexing" width="750"/>
</p>

---

### 💬 Ask Questions About Your Codebase

CodebaseIQ uses Retrieval-Augmented Generation (RAG) to search the indexed repository and provide context-aware answers.

Users can ask questions such as:

* What does this project do?
* What technologies are used?
* Explain a particular function.
* How does the backend work?
* Where is a specific feature implemented?

The response includes relevant source references from the repository.

<p align="center">
  <img src="assets/qa.png" alt="Codebase Q&A" width="750"/>
</p>

---

### 🐛 AI-Powered Bug Finder

The Bug Finder agent analyzes relevant code and identifies potential:

* Bugs
* Security vulnerabilities
* Performance issues
* Code-quality concerns

The agent provides structured findings along with references to the relevant source files and lines.

<p align="center">
  <img src="assets/bug-finder.png" alt="AI Bug Finder" width="750"/>
</p>

---

### 📚 Documentation Generator

The Documentation agent analyzes the codebase and generates explanations for important functions and components.

It can provide information about:

* Function responsibilities
* Implementation logic
* Inputs and outputs
* Overall workflow
* Supporting implementation evidence

<p align="center">
  <img src="assets/documentation.png" alt="Documentation Generation" width="750"/>
</p>

---

## 🧠 How It Works

```text
GitHub Repository
       │
       ▼
Repository Indexing
       │
       ▼
Code & Documentation Chunking
       │
       ▼
Embedding Generation
       │
       ▼
ChromaDB Vector Store
       │
       ▼
Semantic Retrieval
       │
       ▼
      AI Router
   ┌──────┼──────┐
   ▼      ▼      ▼
 Q&A   Bug Finder  Docs
 Agent    Agent    Agent
```

---

## 🛠️ Tech Stack

### Frontend

* React
* JavaScript
* CSS

### Backend

* FastAPI
* Python
* Pydantic

### AI & RAG

* Sentence Transformers
* `all-MiniLM-L6-v2`
* ChromaDB
* Groq API
* Llama 3.3

### Repository Processing

* GitHub repository cloning
* AST-based chunking for Python files
* Line-based chunking for other source files
* Semantic vector search

---

## 🤖 AI Agents

### 💬 Q&A Agent

Answers questions about the indexed repository using retrieved code context.

### 🐛 Bug Finder Agent

Analyzes code for potential bugs, security concerns, and performance issues.

### 📄 Documentation Agent

Generates documentation and explanations for important functions and components.

---

## 🔄 Application Workflow

```text
1. User logs into CodebaseIQ
        ↓
2. User provides a GitHub repository URL
        ↓
3. Repository is cloned and processed
        ↓
4. Code files are split into meaningful chunks
        ↓
5. Embeddings are generated
        ↓
6. Vectors are stored in ChromaDB
        ↓
7. User asks a question or requests analysis
        ↓
8. Relevant code chunks are retrieved
        ↓
9. Request is routed to the appropriate AI agent
        ↓
10. AI-generated response is returned with source references
```

---

## 📂 Project Structure

```text
CodebaseIQ
│
├── backend/
│   ├── agents/
│   │   ├── qa_agent.py
│   │   ├── bug_finder.py
│   │   └── docs_writer.py
│   │
│   ├── services/
│   ├── utils/
│   └── main.py
│
├── frontend/
│   ├── src/
│   └── components/
│
├── assets/
│   ├── login.png
│   ├── codebase-home.png
│   ├── qa.png
│   ├── bug-finder.png
│   └── documentation.png
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd CodebaseIQ
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**macOS/Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on `.env.example`.

```env
GROQ_API_KEY=your_api_key_here
```

### 5. Start the backend

```bash
uvicorn backend.main:app --reload
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 Example Queries

Try asking:

```text
What does this project do?
```

```text
What technologies are used in the frontend and backend?
```

```text
Are there any bugs or security issues?
```

```text
Generate documentation for the main functions.
```

---

## 🔮 Future Improvements

* Multi-language code analysis
* More specialized AI agents
* GitHub OAuth integration
* Real-time repository updates
* Improved bug severity classification
* Repository visualization
* Conversation history
* Support for larger repositories

---

## 👩‍💻 Author

**Tarandeep Kaur**

Built as an AI-powered platform for intelligent codebase understanding, analysis, and documentation.

---

<div align="center">

⭐ If you find this project interesting, consider giving it a star!

</div>
