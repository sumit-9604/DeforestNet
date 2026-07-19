import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from backend.database.database import get_db
from backend.models.alert import Alert, RegionOfInterest, AlertResponse, AlertUpdateStatus
from backend.models.report import Report
from backend.services.data_ingestion import DataIngestionService
from backend.services.change_detection import ChangeDetectionService
from backend.services.context_enrichment import ContextEnrichmentService
from backend.services.llm_reasoning import LLMReasoningService
from backend.services.report_generator import ReportGeneratorService
from backend.services.notification import NotificationService
from backend.utils.logger import setup_logger
from backend.utils.image_processing import generate_comparison_image
import numpy as np

logger = setup_logger("api_alerts")
router = APIRouter()

@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    region_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Retrieve all alerts with optional filtering"""
    query = db.query(Alert)
    
    if status:
        query = query.filter(Alert.status == status)
    if risk_level:
        query = query.filter(Alert.risk_level == risk_level)
    if region_id:
        query = query.filter(Alert.region_id == region_id)
        
    return query.order_by(Alert.detected_at.desc()).all()

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert_detail(alert_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a single alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert_status(alert_id: int, payload: AlertUpdateStatus, db: Session = Depends(get_db)):
    """Manually update the status and risk level of an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if payload.risk_level:
        alert.risk_level = payload.risk_level

    # Authorization is a report-delivery action, not an alert state of its own.
    # Persist both records so the Reports UI remains correct after a refresh.
    if payload.status in ["Authorized", "Reported"]:
        report = db.query(Report).filter(Report.alert_id == alert.id).order_by(Report.generated_at.desc()).first()
        if not report:
            raise HTTPException(status_code=409, detail="No evidence report exists for this alert")

        import os
        from backend.config import REPORTS_DIR

        pdf_path = report.file_path
        # Resolve report paths created on another operating system.
        if not os.path.exists(pdf_path):
            filename = os.path.basename(pdf_path.replace("\\", "/"))
            local_path = REPORTS_DIR / filename
            if local_path.exists():
                pdf_path = str(local_path)

        notifier = NotificationService()
        sent = notifier.send_report_notification(
            recipient_email=report.recipient_email,
            alert_id=alert.id,
            pdf_path=pdf_path
        )
        report.status = "Sent" if sent else "Failed"
        alert.status = "Reported" if sent else "Verified"
    else:
        alert.status = payload.status

    db.commit()
    db.refresh(alert)
    return alert

@router.post("/trigger-check")
def trigger_agent_check(region_name: str = "Amazon Wildlife Reserve", human_oversight: bool = True, db: Session = Depends(get_db)):
    """
    Triggers the autonomous agent pipeline for a Region of Interest.
    """
    logger.info(f"Manual trigger received for pipeline check in region: {region_name} (Human oversight: {human_oversight})")
    
    # 1. Fetch Region
    region = db.query(RegionOfInterest).filter(RegionOfInterest.name == region_name).first()
    if not region:
        # Create standard region if missing
        logger.info(f"Region {region_name} not found. Creating default seed record.")
        if "Amazon" in region_name:
            geom = '{"type": "Polygon", "coordinates": [[[-62.3, -3.55], [-62.1, -3.55], [-62.1, -3.35], [-62.3, -3.35], [-62.3, -3.55]]]}'
            email = "amazon-alerts@conservation.org"
        else:
            geom = '{"type": "Polygon", "coordinates": [[[116.8, -1.35], [117.0, -1.35], [117.0, -1.15], [116.8, -1.15], [116.8, -1.35]]]}'
            email = "kalimantan-office@deforestnet.org"
            
        region = RegionOfInterest(name=region_name, geometry=geom, contact_email=email)
        db.add(region)
        db.commit()
        db.refresh(region)

    # 2. Instantiate and run autonomous agent
    from backend.agent.agent import DeForestNetAgent
    
    try:
        agent = DeForestNetAgent()
        metrics = agent.run(region_name, db, human_oversight=human_oversight)
        
        return {
            "status": "Success",
            "region": region_name,
            "raw_alerts_received": metrics.get("raw_alerts_received", 0),
            "new_alerts_processed": metrics.get("new_alerts_processed", 0),
            "verified_deforestation_events": metrics.get("verified_deforestation_events", 0),
            "evidence_reports_dispatched": metrics.get("evidence_reports_dispatched", 0)
        }
    except Exception as e:
        logger.error(f"Agent pipeline failed for region {region_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent pipeline execution failed: {str(e)}")

@router.get("/{alert_id}/image/{timeframe}")
def get_alert_timeframe_image(alert_id: int, timeframe: str, db: Session = Depends(get_db)):
    """Serves before or after satellite image as PNG processed on the fly"""
    from backend.config import IMAGERY_DIR
    from backend.utils.image_processing import contrast_stretch
    from fastapi import Response
    from PIL import Image
    import cv2
    import io
    
    if timeframe not in ("before", "after"):
        raise HTTPException(status_code=400, detail="Invalid timeframe. Must be 'before' or 'after'.")
        
    npy_path = IMAGERY_DIR / f"alert_{alert_id}" / timeframe / "rgb.npy"
    if not npy_path.exists():
        raise HTTPException(status_code=404, detail=f"Satellite imagery not found for alert {alert_id} ({timeframe})")
        
    try:
        bgr = np.load(str(npy_path))
        # Stretched BGR
        stretched = contrast_stretch(bgr)
        # Convert to PNG bytes
        rgb = cv2.cvtColor(stretched, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        logger.error(f"Error serving timeframe image for alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing image")

@router.get("/{alert_id}/comparison")
def get_alert_comparison_image(alert_id: int, db: Session = Depends(get_db)):
    """Serves the generated 2x2 comparison image for an alert"""
    from backend.config import IMAGERY_DIR
    from fastapi.responses import FileResponse
    comp_path = IMAGERY_DIR / f"alert_{alert_id}" / "comparison.png"
    if not comp_path.exists():
        raise HTTPException(status_code=404, detail="Comparison image not found for this alert")
    return FileResponse(str(comp_path), media_type="image/png")
