# AskRepo API

A high-performance, RAG-powered (Retrieval-Augmented Generation) backend that ingests GitHub repositories and allows users to chat with codebases in real-time. 

Built with **FastAPI**, **PostgreSQL**, **Celery**, and **OpenAI API**, this API is designed for speed, concurrency, and production-grade reliability.

## Features

* **Real-Time Streaming:** Uses Server-Sent Events (SSE) to stream LLM responses token-by-token.
* **Intelligent Routing:** An AI router sits ahead of the RAG pipeline, instantly deciding whether a user's query requires a fresh vector search or if it can be answered using the sliding window of conversation history.
* **Asynchronous Engine:** Fully async endpoints and LLM clients (`AsyncOpenAI`) prevent blocking under heavy concurrent load.
* **Background Processing:** Heavy tasks (cloning repos, text chunking, and vector embedding via `BAAI/bge-small-en-v1.5`) are offloaded to **Celery + Redis** workers.
* **Security & Validation:** * Strict Pydantic URL sanitization prevents injection attacks.
  * Integration with the GitHub API to proactively block repositories over 20MB before they exhaust server memory.
  * IP-based Rate Limiting via `slowapi` to protect expensive endpoints.
* **UX-First Design:** Calculates and returns intelligent Time-to-Completion (ETA) estimates for repo indexing. Background generation of chat titles keeps the main thread fast.

## Architecture

- **Web Framework:** FastAPI
- **Database:** PostgreSQL (with `pgvector` for similarity search) via SQLAlchemy
- **Message Broker:** Redis
- **Task Queue:** Celery
- **LLM Provider:** OpenAI
- **Embeddings:** Local SentenceTransformers (`bge-small-en-v1.5`)
- **Deployment:** Docker Compose, AWS EC2, nginx

## Quick Start (Local Development)

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.12+
- A DeepSeek API Key

### 2. Environment Variables
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

### 3. Run with Docker Compose
docker compose up -d --build
