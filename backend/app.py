from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer

from agents.orchestrator import RAGOrchestrator
from database import engine, Base
from api.routers import index, query, auth_router, conversations
from api.limiter import limiter
from config import settings
from logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- Starting Codebase RAG Application ---")

    try:
        logger.info("Initializing database tables...")
        # Create the database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database connection and tables verified.")

        logger.info("Loading Embedding Model (BAAI/bge-small-en-v1.5)...")
        embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

        logger.info("Initializing RAG Orchestrator...")
        app.state.orchestrator = RAGOrchestrator(embedding_model=embedding_model)

        logger.info("Application startup complete. Ready for requests.")
    except Exception as e:
        logger.critical(f"Startup failed: {str(e)}", exc_info=True)
        raise e

    yield
    
    logger.info("Shutting down application...")

app = FastAPI(title="Codebase RAG API", lifespan=lifespan)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

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


