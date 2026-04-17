from config import settings
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class IndexTask(Base):
    __tablename__ = "index_tasks"
    id = Column(String, primary_key=True, index=True)
    repo_name = Column(String, index=True)
    status = Column(String, default="PENDING")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
