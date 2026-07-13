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

    # 2. Instantiate pipeline services
    ingestion_service = DataIngestionService()
    detection_service = ChangeDetectionService()
    enrichment_service = ContextEnrichmentService()
    reasoning_service = LLMReasoningService()
    report_service = ReportGeneratorService()
    notification_service = NotificationService()
    
    # 3. Ingest raw alerts
    raw_alerts = ingestion_service.fetch_deforestation_alerts(region_name)
    processed_count = 0
    verified_count = 0
    reports_count = 0
    
    for alert_data in raw_alerts:
        lat = alert_data["latitude"]
        lon = alert_data["longitude"]
        area_ha = alert_data["area_ha"]
        
        # Check if identical alert coordinates exist in database to avoid duplicate checks
        # Tolerance ~ 100 meters (0.001 degrees)
        exists = db.query(Alert).filter(
            Alert.latitude.between(lat - 0.001, lat + 0.001),
            Alert.longitude.between(lon - 0.001, lon + 0.001),
            Alert.status != "False Positive"
        ).first()
        
        if exists:
            logger.info(f"Alert at ({lat:.4f}, {lon:.4f}) already exists (ID: {exists.id}). Skipping reprocessing.")
            continue
            
        processed_count += 1
        
        # Create initial Alert DB record
        alert_db = Alert(
            region_id=region.id,
            latitude=lat,
            longitude=lon,
            area_ha=area_ha,
            status="Pending",
            details=alert_data["details"]
        )
        db.add(alert_db)
        db.commit()
        db.refresh(alert_db)
        
        try:
            # 4. Fetch satellite imagery
            imagery_paths = ingestion_service.fetch_satellite_imagery(lat, lon, alert_db.id)
            alert_db.imagery_before_path = imagery_paths["before"]["rgb"]
            alert_db.imagery_after_path = imagery_paths["after"]["rgb"]
            
            # 5. Run change detection (NDVI comparison)
            change_data = detection_service.detect_changes(imagery_paths, area_ha)
            alert_db.ndvi_before = change_data["ndvi_before_mean"]
            alert_db.ndvi_after = change_data["ndvi_after_mean"]
            alert_db.ndvi_diff = change_data["verified_area_ha"]  # Save verified area ha into diff field or custom
            
            if not change_data["is_verified"]:
                logger.info(f"Change detection filtered alert {alert_db.id} as a False Positive.")
                alert_db.status = "False Positive"
                alert_db.risk_level = "Low"
                db.commit()
                continue
                
            verified_count += 1
            alert_db.status = "Verified"
            
            # 6. Context enrichment (WDPA boundaries, spatial clusters)
            enrichment_data = enrichment_service.enrich_alert_context(alert_db, db)
            
            # Combine alert variables to pass to LLM
            llm_input = {
                "latitude": lat,
                "longitude": lon,
                "area_ha": change_data["verified_area_ha"],
                "ndvi_before_mean": change_data["ndvi_before_mean"],
                "ndvi_after_mean": change_data["ndvi_after_mean"],
                "ndvi_diff_mean": change_data["ndvi_diff_mean"],
                "is_protected": enrichment_data["is_protected"],
                "protected_area_name": enrichment_data["protected_area_name"],
                "protected_area_category": enrichment_data["protected_area_category"],
                "is_active_cluster": enrichment_data["is_active_cluster"],
                "neighboring_alerts_30d": enrichment_data["neighboring_alerts_30d"]
            }
            
            # 7. LLM Reasoning & Assessment
            llm_result = reasoning_service.analyze_alert(llm_input)
            alert_db.risk_level = llm_result.get("risk_level", "Medium")
            
            # Save LLM details in JSON
            full_details = json.loads(alert_db.details) if alert_db.details else {}
            full_details.update({
                "protected_info": {
                    "is_protected": enrichment_data["is_protected"],
                    "name": enrichment_data["protected_area_name"]
                },
                "spatial_cluster": {
                    "neighboring_alerts_30d": enrichment_data["neighboring_alerts_30d"],
                    "is_active_cluster": enrichment_data["is_active_cluster"]
                },
                "reasoning_chain": llm_result.get("reasoning_chain")
            })
            alert_db.details = json.dumps(full_details)
            
            # 8. Generate 4-panel comparative image
            # Load images
            b_rgb = np.load(imagery_paths["before"]["rgb"])
            a_rgb = np.load(imagery_paths["after"]["rgb"])
            comp_img_path = str(Path(alert_db.imagery_before_path).parent.parent / "comparison.png")
            
            generate_comparison_image(
                before_rgb=b_rgb,
                after_rgb=a_rgb,
                before_ndvi=change_data["before_ndvi_array"],
                after_ndvi=change_data["after_ndvi_array"],
                deforestation_mask=change_data["deforestation_mask"],
                save_path=comp_img_path
            )
            
            # 9. Compile PDF Report
            pdf_path = report_service.generate_pdf_report(alert_db, llm_result, comp_img_path)
            
            # Create report record
            report_db = Report(
                alert_id=alert_db.id,
                file_path=pdf_path,
                narrative_summary=llm_result.get("narrative_summary", ""),
                recommended_action=llm_result.get("recommended_action", ""),
                recipient_email=region.contact_email,
                status="Pending"
            )
            db.add(report_db)
            db.commit()
            
            # 10. Route Dispatch
            sent = notification_service.send_report_notification(
                recipient_email=region.contact_email,
                alert_id=alert_db.id,
                pdf_path=pdf_path
            )
            
            if sent:
                report_db.status = "Sent"
                alert_db.status = "Reported"
                reports_count += 1
            else:
                report_db.status = "Failed"
                alert_db.status = "Verified"
                
            db.commit()
            
        except Exception as e:
            logger.error(f"Error executing agent pipeline for alert {alert_db.id}: {e}", exc_info=True)
            db.rollback()
            
    return {
        "status": "Success",
        "region": region_name,
        "raw_alerts_received": len(raw_alerts),
        "new_alerts_processed": processed_count,
        "verified_deforestation_events": verified_count,
        "evidence_reports_dispatched": reports_count
    }
