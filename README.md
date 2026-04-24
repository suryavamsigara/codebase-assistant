# AskRepo - Codebase Assistant

An intelligent, full-stack application that allows users to chat with any public GitHub repository.

By combining abstract syntax tree (AST) parsing, hybrid vector search, and real-time LLM streaming, this tool acts as an expert pair programmer that actually understands your entire codebase.

![askrepo UI](askrepo_ui_image.bmp)

## Features

- **Smart Code Chunking** - Uses Tree-sitter parsers for Python and JavaScript/JSX to extract functions, classes, methods, and docstrings with full context.
- **Hybrid Retrieval** - Combines vector search (BGE-small embeddings + pgvector) and BM25 keyword search with Reciprocal Rank Fusion (RRF) for best-in-class relevance.
- **Streaming AI Answers** - Real-time token streaming with citations.
- **Background Indexing** - Clone and index any public GitHub repo via Celery + Redis (non-blocking).
- **Conversation System** - Persistent chats with auto-generated titles and history.
- **Authentication** - Full JWT auth + seamless guest mode (localStorage).
- **File Viewer** - Click any citation to view the complete source file.
- **Modern UI** - Beautiful React + Framer Motion interface with sidebar, zero-state, and dark mode.
- **Production Ready** — Dockerized Postgres + Redis, and logging

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL + pgvector (vector + full-text search)
- **Embeddings**: `BAAI/bge-small-en-v1.5` via Sentence-Transformers
- **Parsing**: Tree-sitter (Python + JavaScript)
- **Task Queue**: Celery + Redis
- **Auth**: JWT + bcrypt
- **ORM**: SQLAlchemy 2.0

### Frontend
- **Framework**: React + TypeScript
- **Routing**: React Router v6
- **Styling**: Tailwind CSS + custom dark mode
- **Animations**: Framer Motion
- **Streaming**: Server-Sent Events (SSE)

## Project Structure

```text
.
├── backend/                  # FastAPI Application
│   ├── agents/               # LLM Orchestrator, Router, and Answer Agents
|   ├── indexing/             # Walker, Chunker, embeddings, pipeline
|   ├── retrieval/            # RRF
│   ├── api/                  # REST/SSE endpoints, Schemas, and Utils
│   ├── core/                 # Database setup, Models, and Config
│   ├── celery_worker.py      # Background ingestion and AST parsing
|   ├── app.py
|   ├── models.py
|   ├── config.py
|   ├── database.py
│   ├── Dockerfile
|   ├── docker-compose.yml    # Infrastructure setup (Postgres, Redis, API, Worker)
│   └── pyproject.toml
├── frontend/                 # React Application
│   ├── src/
│   │   ├── components/       # Chat interface, Sidebar, and Markdown renderers
│   │   └── utils/
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## Quick Start (Local Development)

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.12+

### 2. Clone the repository
```
git clone https://github.com/suryavamsigara/codebase-assistant.git
cd codebase-assistant
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```env
DEEPSEEK_API_KEY=your_deepseek_key_here

DATABASE_HOSTNAME=..
DATABASE_PORT=5432
DATABASE_PASSWORD=..
DATABASE_NAME=..
DATABASE_USERNAME=..

SECRET_KEY=..
ALGORITHM=HS256
redis_url=redis://redis:6379/0
```

### 4. Start the backend infrastructure
```
docker compose up -d --build
```

### 5. Start the frontend
```
cd frontend
npm install
npm run dev
```
The React application will be available at `http://localhost:5173`

## Usage
- Index a repository by pasting GitHub URL
- Once indexing is completem, chat with the codebase
- Explore citations. Click the hyperlinked files in the resopnse to open them.