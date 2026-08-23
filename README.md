# 🚀 CodebaseIQ

<div align="center">

### Understand Any Codebase, Instantly

An AI-powered platform that helps developers understand, analyze, and interact with GitHub repositories using **Retrieval-Augmented Generation (RAG)** and specialized AI agents.

</div>

---

## 📌 Overview

Understanding an unfamiliar codebase can be time-consuming, especially when working with large projects containing multiple files, functions, and dependencies.

**CodebaseIQ** simplifies this process by allowing users to index a GitHub repository and interact with its codebase through AI-powered agents.

The platform can:

* 📂 Index GitHub repositories
* 💬 Answer questions about the codebase
* 🐛 Analyze code for potential bugs and issues
* 📚 Generate documentation for important functions
* 🔍 Retrieve relevant code using semantic search

---

# ✨ Features

## 🔐 User Authentication

Users can securely sign in to access the CodebaseIQ platform.

<p align="center">
  <img src="assets/login.png" alt="CodebaseIQ Login" width="600"/>
</p>

---

## 📂 Repository Indexing

Users can provide a GitHub repository URL and index the repository.

During indexing, the repository is processed and its source files are prepared for semantic search and AI-powered analysis.

Indexed repositories are displayed in the sidebar and can be selected for further interaction.

<p align="center">
  <img src="assets/indexing.png" alt="Repository Indexing" width="800"/>
</p>

---

## 💬 Codebase Q&A Agent

The Q&A agent allows users to ask questions about the indexed repository.

The system retrieves relevant code chunks and uses them as context to generate grounded answers.

Example questions include:

* What does this project do?
* What technologies are used?
* Explain the backend architecture.
* How does a particular function work?
* Where is a specific feature implemented?

<p align="center">
  <img src="assets/quesansagent.png" alt="Codebase Q&A Agent" width="800"/>
</p>

---

## 🐛 Bug Finder Agent

The Bug Finder agent analyzes the relevant source code and identifies potential:

* Bugs
* Security vulnerabilities
* Performance issues
* Code-quality concerns

The generated response is supported by references to relevant files and code sections.

<p align="center">
  <img src="assets/bugagent.png" alt="Bug Finder Agent" width="800"/>
</p>

---

## 📚 Documentation Agent

The Documentation Agent analyzes important functions and generates structured documentation explaining their purpose and implementation.

It can provide insights into:

* Function responsibilities
* Core implementation logic
* Inputs and outputs
* Application workflow
* Supporting code references

<p align="center">
  <img src="assets/docsagent.png" alt="Documentation Agent" width="800"/>
</p>

---

# 🧠 How It Works

```text
GitHub Repository
       │
       ▼
Repository Indexing
       │
       ▼
Code & Documentation Processing
       │
       ▼
Code Chunking
       │
       ▼
Embedding Generation
       │
       ▼
ChromaDB Vector Store
       │
       ▼
Semantic Search & Retrieval
       │
       ▼
AI Agent Routing
   ┌──────┼──────┐
   ▼      ▼      ▼
 Q&A   Bug Finder  Docs
 Agent    Agent    Agent
```

---

# 🛠️ Tech Stack

## Frontend

* React
* JavaScript
* HTML
* CSS

## Backend

* Python
* FastAPI
* Pydantic

## AI & RAG

* Groq API
* Llama 3.3
* Sentence Transformers
* `all-MiniLM-L6-v2`
* ChromaDB

## Repository Processing

* GitHub repository cloning
* AST-based code chunking
* Line-based chunking
* Semantic vector search

---

# 🤖 AI Agents

## 💬 Q&A Agent

The Q&A Agent retrieves relevant code chunks from the indexed repository and generates answers based on the retrieved context.

## 🐛 Bug Finder Agent

The Bug Finder Agent analyzes source code and identifies potential bugs, security concerns, and performance issues.

## 📚 Documentation Agent

The Documentation Agent generates explanations and documentation for important functions and components within the repository.

---

# 🔄 Application Workflow

```text
1. User signs in to CodebaseIQ
        ↓
2. User provides a GitHub repository URL
        ↓
3. Repository is cloned and indexed
        ↓
4. Source files are processed
        ↓
5. Code is divided into meaningful chunks
        ↓
6. Embeddings are generated
        ↓
7. Vectors are stored in ChromaDB
        ↓
8. User submits a query or analysis request
        ↓
9. Relevant code chunks are retrieved
        ↓
10. Request is routed to the appropriate AI agent
        ↓
11. AI-generated response is returned with source references
```

---

# 📂 Project Structure

```text
CodebaseIQ/
│
├── assets/
│   ├── bugagent.png
│   ├── docsagent.png
│   ├── indexing.png
│   ├── login.png
│   └── quesansagent.png
│
├── backend/
│   ├── agents/
│   ├── services/
│   ├── utils/
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── components/
│   └── ...
│
├── requirements.txt
├── .env.example
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Tarandeepkaur88/CodebaseIQ.git
cd CodebaseIQ
```

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

## 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file based on the `.env.example` file.

Add your required API keys:

```env
GROQ_API_KEY=your_groq_api_key
```

---

## 5. Start the Backend

```bash
uvicorn backend.main:app --reload
```

The backend should start locally and expose the API endpoints.

---

## 6. Start the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your browser.

---

# 💡 Example Queries

You can ask CodebaseIQ questions such as:

```text
What does this project do?
```

```text
What technologies are used in the frontend and backend?
```

```text
How does repository indexing work?
```

```text
Are there any bugs or security issues?
```

```text
Generate documentation for the main functions.
```

---

# 🚀 Key Concepts Used

* **Retrieval-Augmented Generation (RAG)**
* **Semantic Search**
* **Vector Embeddings**
* **Vector Database**
* **AST-Based Code Chunking**
* **Large Language Models**
* **AI Agents**
* **FastAPI**
* **React**

---

# 🔮 Future Improvements

* [ ] Support for additional programming languages
* [ ] Improved multi-agent routing
* [ ] More advanced bug severity classification
* [ ] Repository architecture visualization
* [ ] Conversation history
* [ ] Support for larger repositories
* [ ] Real-time repository updates
* [ ] Additional AI-powered code analysis agents

---

# 👩‍💻 Author

**Tarandeep Kaur**

Built as an AI-powered platform for intelligent codebase understanding, analysis, bug detection, and automated documentation.

---

<div align="center">

⭐ If you found this project interesting, consider giving it a star!

</div>
