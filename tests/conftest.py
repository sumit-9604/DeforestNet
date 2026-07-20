import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Create a temporary directory for test storage (imagery, reports)
test_storage_dir = tempfile.mkdtemp()
os.environ["STORAGE_DIR"] = test_storage_dir
os.environ["LLM_PROVIDER"] = "mock"
os.environ["SIMULATION_MODE"] = "True"

# Add project root to sys.path to ensure correct imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database.database import Base, get_db
from backend.app import app

# Create in-memory SQLite database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    # Import models to register metadata
    from backend.models.user import User
    from backend.models.alert import Alert, RegionOfInterest
    from backend.models.report import Report
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up temporary test storage folder
    shutil.rmtree(test_storage_dir, ignore_errors=True)

@pytest.fixture
def db_session():
    # Connect and create session
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Seed standard database data
    from backend.database.seed import seed_database
    seed_database(session)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
