import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from backend.database.database import get_db
from backend.models.report import Report, ReportResponse
from backend.utils.logger import setup_logger
from backend.config import REPORTS_DIR

logger = setup_logger("api_reports")
router = APIRouter()

@router.get("/", response_model=List[ReportResponse])
def get_reports(db: Session = Depends(get_db)):
    """Retrieve list of all compiled reports"""
    return db.query(Report).order_by(Report.generated_at.desc()).all()

@router.get("/{report_id}/download")
def download_pdf_report(report_id: int, db: Session = Depends(get_db)):
    """Downloads the compiled PDF file for the given report ID"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    pdf_path = report.file_path
    
    # Check if file exists locally. If not, resolve the file's basename inside the local REPORTS_DIR or repository folder
    if not os.path.exists(pdf_path):
        filename = os.path.basename(pdf_path.replace("\\", "/"))
        local_path = REPORTS_DIR / filename
        if local_path.exists():
            pdf_path = str(local_path)
        else:
            from backend.config import BASE_DIR
            repo_path = BASE_DIR / "storage" / "reports" / filename
            if repo_path.exists():
                pdf_path = str(repo_path)
            else:
                logger.error(f"Report file missing on disk: {pdf_path} (Checked local fallback: {local_path} and repository fallback: {repo_path})")
                raise HTTPException(status_code=404, detail="PDF report file does not exist on disk")
        
    # Return FileResponse to trigger browser download/preview
    filename = os.path.basename(pdf_path)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename
    )
