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
            # Dynamically regenerate the PDF report if it's missing (e.g., due to ephemeral Render disk)
            try:
                logger.info(f"PDF report file missing on disk. Attempting to dynamically regenerate for report ID: {report_id} to path: {local_path}")
                from backend.services.report_generator import ReportGeneratorService
                import json
                from backend.config import IMAGERY_DIR
                
                alert = report.alert
                if not alert:
                    raise ValueError("Alert associated with the report not found")
                    
                details = json.loads(alert.details) if alert.details else {}
                protected_info = details.get("protected_info", {})
                spatial_cluster = details.get("spatial_cluster", {})
                
                analysis_result = {
                    "risk_level": alert.risk_level or "Medium",
                    "narrative_summary": report.narrative_summary,
                    "recommended_action": report.recommended_action,
                    "is_protected": protected_info.get("is_protected", False),
                    "protected_area_name": protected_info.get("name", ""),
                    "neighboring_alerts_30d": spatial_cluster.get("neighboring_alerts_30d", 0)
                }
                
                comp_img_path = str(IMAGERY_DIR / f"alert_{alert.id}" / "comparison.png")
                reporter = ReportGeneratorService()
                pdf_path = reporter.generate_pdf_report(alert, analysis_result, comp_img_path, custom_filename=filename)
            except Exception as e:
                logger.error(f"Failed to dynamically regenerate PDF report: {e}", exc_info=True)
                raise HTTPException(status_code=404, detail="PDF report file does not exist on disk and regeneration failed")
        
    # Return FileResponse to trigger browser download/preview
    filename = os.path.basename(pdf_path)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename
    )
