from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer

from agents.orchestrator import RAGOrchestrator
from database import engine, Base
from api.routers import index, query, auth_router, conversations

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting application..")

    print("Connecting to database...")
    # Create the database tables
    Base.metadata.create_all(bind=engine)

    print("Loading Embedding Model...")
    embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    app.state.orchestrator = RAGOrchestrator(embedding_model=embedding_model)

    print("App ready.")
    yield

    print("Shutting down...")

app = FastAPI(title="Codebase RAG API", lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1_prefix = "/api/v1"

@app.get("/")
def health_check():
    return {"status": "operational", "service": "Codebase Assistant"}

app.include_router(index.router, prefix=api_v1_prefix)
app.include_router(query.router, prefix=api_v1_prefix)
app.include_router(auth_router.router, prefix=api_v1_prefix)
app.include_router(conversations.router, prefix=api_v1_prefix)


