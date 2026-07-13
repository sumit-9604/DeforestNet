import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL

# configure sqlite database path and settings
# check_same_thread: False is required for SQLite in multi-threaded FastAPI apps
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database by creating tables from schema.sql or SQLAlchemy metadata"""
    # Import models here to register them with metadata
    from backend.models.user import User
    from backend.models.alert import Alert
    from backend.models.report import Report
    
    # We can use metadata to create all tables
    Base.metadata.create_all(bind=engine)
    
    # Check if schema.sql should be run directly for custom constraints/types
    # SQLite can just run the metadata creation, but let's run the schema.sql
    # file if it exists to ensure any custom sql runs, but create_all is usually cleaner.
    # We'll stick with create_all for standard ORM initialization.
