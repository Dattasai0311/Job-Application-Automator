from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True)
    title = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    ats_type = Column(String) # 'greenhouse', 'lever', 'workday', etc.
    description = Column(Text)
    status = Column(String, default="new") # 'new', 'queued', 'applied', 'failed', 'rejected'
    date_found = Column(DateTime, default=datetime.utcnow)
    date_applied = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

# Ensure db directory exists
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "db")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "jobs.db")

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)
