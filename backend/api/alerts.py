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
        
    alert.status = payload.status
    if payload.risk_level:
        alert.risk_level = payload.risk_level
        
    db.commit()
    db.refresh(alert)
    return alert

@router.post("/trigger-check")
def trigger_agent_check(region_name: str = "Amazon Wildlife Reserve", db: Session = Depends(get_db)):
    """
    Triggers the autonomous agent pipeline for a Region of Interest.
    Steps:
      1. Query region from database (fallback to auto-creating it if not seeded)
      2. Ingest alerts from GFW API / Simulation
      3. For each alert, check for duplicates:
         - Calculate NDVI changes on satellite imagery
         - Enrich context with protected area bounds & clustering
         - Invoke LLM Reasoning for risk rating & narrative
         - Generate comparative image grids
         - Compile PDF report
         - Route dispatch to authority contact
         - Persist status updates in database
    """
    logger.info(f"Manual trigger received for pipeline check in region: {region_name}")
    
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
            email = "kalimantan-office@forestguard.org"
            
        region = RegionOfInterest(name=region_name, geometry=geom, contact_email=email)
        db.add(region)
        db.commit()
        db.refresh(region)

    # 2. Instantiate and run autonomous agent
    from backend.agent.agent import ForestGuardAgent
    
    try:
        agent = ForestGuardAgent()
        metrics = agent.run(region_name, db)
        
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
