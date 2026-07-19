import json
from sqlalchemy.orm import Session
from backend.database.database import engine, Base, SessionLocal
from backend.models.user import User
from backend.models.alert import RegionOfInterest, Alert
from backend.models.report import Report
from backend.utils.logger import setup_logger

logger = setup_logger("db_seed")

def hash_password(password: str) -> str:
    # A simple mock password hashing function for demonstration/sandbox purposes.
    # In a full production system, we'd use passlib/bcrypt.
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database(db: Session):
    """Seed regions of interest and standard user accounts"""
    logger.info("Starting database seeding...")
    
    # 1. Seed Users
    existing_users = db.query(User).count()
    if existing_users == 0:
        logger.info("Seeding user accounts...")
        users = [
            User(
                email="admin@deforestnet.org",
                password_hash=hash_password("admin123"),
                role="Admin"
            ),
            User(
                email="researcher@deforestnet.org",
                password_hash=hash_password("researcher123"),
                role="Researcher"
            ),
            User(
                email="officer@deforestnet.org",
                password_hash=hash_password("officer123"),
                role="Authority"
            )
        ]
        db.add_all(users)
        db.commit()
        logger.info("Successfully seeded users.")
    else:
        logger.info("Users table is not empty. Skipping seeding users.")

    # 2. Seed Regions of Interest
    existing_regions = db.query(RegionOfInterest).count()
    if existing_regions == 0:
        logger.info("Seeding regions of interest...")
        
        amazon_geom = {
            "type": "Polygon",
            "coordinates": [[
                [-62.30, -3.55],
                [-62.10, -3.55],
                [-62.10, -3.35],
                [-62.30, -3.35],
                [-62.30, -3.55]
            ]]
        }
        
        kalimantan_geom = {
            "type": "Polygon",
            "coordinates": [[
                [116.80, -1.35],
                [117.00, -1.35],
                [117.00, -1.15],
                [116.80, -1.15],
                [116.80, -1.35]
            ]]
        }
        
        regions = [
            RegionOfInterest(
                name="Amazon Wildlife Reserve",
                geometry=json.dumps(amazon_geom),
                contact_email="amazon-officer@deforestnet.org"
            ),
            RegionOfInterest(
                name="Kalimantan Protected Forest",
                geometry=json.dumps(kalimantan_geom),
                contact_email="kalimantan-officer@deforestnet.org"
            )
        ]
        db.add_all(regions)
        db.commit()
        logger.info("Successfully seeded regions.")
    else:
        logger.info("Regions of interest table is not empty. Skipping seeding regions.")

    logger.info("Database seeding complete.")

if __name__ == "__main__":
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Seed
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
