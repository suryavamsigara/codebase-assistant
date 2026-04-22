# Codebase Assistant

Ask natural-language questions about your codebase and get accurate, context-aware answers with direct citations to functions, classes, and files.

Built as a full-stack application with semantic code understanding, hybrid search, streaming responses, conversation history, and support for both authenticated users and guests.

## Features

- **Smart Code Chunking** — Uses Tree-sitter parsers for Python and JavaScript/JSX to extract functions, classes, methods, and docstrings with full context.
- **Hybrid Retrieval** — Combines vector search (BGE-small embeddings + pgvector) and BM25 keyword search with Reciprocal Rank Fusion (RRF) for best-in-class relevance.
- **Streaming AI Answers** — Real-time token streaming with citations.
- **Background Indexing** — Clone and index any public GitHub repo via Celery + Redis (non-blocking).
- **Conversation System** — Persistent chats with auto-generated titles and history.
- **Authentication** — Full JWT auth + seamless guest mode (localStorage).
- **File Viewer** — Click any citation to view the complete source file.
- **Modern UI** — Beautiful React + Framer Motion interface with sidebar, zero-state, and dark mode.
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
