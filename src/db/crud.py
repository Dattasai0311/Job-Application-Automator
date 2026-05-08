from sqlalchemy.orm import Session
from src.db.models import JobListing
from datetime import datetime

def add_job(db: Session, company: str, title: str, url: str, ats_type: str, description: str = ""):
    db_job = db.query(JobListing).filter(JobListing.url == url).first()
    if db_job:
        return db_job
    
    new_job = JobListing(
        company=company,
        title=title,
        url=url,
        ats_type=ats_type,
        description=description,
        status="new"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

def get_jobs_by_status(db: Session, status: str):
    return db.query(JobListing).filter(JobListing.status == status).all()

def get_all_jobs(db: Session):
    return db.query(JobListing).all()

def update_job_status(db: Session, job_id: int, new_status: str, notes: str = ""):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if job:
        job.status = new_status
        if new_status == "applied":
            job.date_applied = datetime.utcnow()
        if notes:
            job.notes = notes
        db.commit()
        db.refresh(job)
    return job
