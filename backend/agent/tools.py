# Tool definitions for the DeForestNet Agentic Layer

import os
import json
import numpy as np
from pathlib import Path
from backend.services.data_ingestion import DataIngestionService
from backend.services.change_detection import ChangeDetectionService
from backend.services.context_enrichment import ContextEnrichmentService
from backend.services.report_generator import ReportGeneratorService
from backend.services.notification import NotificationService
from backend.utils.geo_utils import check_intersection_with_protected_areas
from backend.utils.image_processing import generate_comparison_image
from backend.utils.ndvi import calculate_ndvi
from backend.models.alert import Alert, RegionOfInterest
from backend.models.report import Report
from backend.utils.logger import setup_logger

logger = setup_logger("agent_tools")


class BaseTool:
    name: str = ""
    description: str = ""

    def run(self, parameters: dict, db=None) -> any:
        raise NotImplementedError


class GetForestAlertsTool(BaseTool):
    name = "GetForestAlertsTool"
    description = "Retrieve latest deforestation alerts for a given region."

    def run(self, parameters: dict, db=None) -> any:
        region_name = parameters.get("region_name", "Amazon Wildlife Reserve")
        logger.info(f"Running GetForestAlertsTool for region: {region_name}")
        ingestion = DataIngestionService()
        alerts = ingestion.fetch_deforestation_alerts(region_name)
        return alerts


class FetchSatelliteImageTool(BaseTool):
    name = "FetchSatelliteImageTool"
    description = "Download pre- and post-clearing satellite bands (Red, NIR, RGB) for GPS coordinates."

    def run(self, parameters: dict, db=None) -> any:
        lat = parameters.get("latitude")
        lon = parameters.get("longitude")
        alert_id = parameters.get("alert_id")
        logger.info(f"Running FetchSatelliteImageTool for alert {alert_id} at ({lat}, {lon})")
        ingestion = DataIngestionService()
        paths = ingestion.fetch_satellite_imagery(lat, lon, alert_id)
        return paths


class ComputeNDVITool(BaseTool):
    name = "ComputeNDVITool"
    description = "Calculate NDVI and detect verified forest/vegetation loss ratio."

    def run(self, parameters: dict, db=None) -> any:
        imagery_paths = parameters.get("imagery_paths")
        area_ha = parameters.get("area_ha")
        logger.info(f"Running ComputeNDVITool for alert area {area_ha}")
        detector = ChangeDetectionService()
        result = detector.detect_changes(imagery_paths, area_ha)
        
        # Strip out numpy arrays before returning to keep results JSON serializable for LLM history
        serializable_result = {
            "is_verified": result.get("is_verified", False),
            "ndvi_before_mean": result.get("ndvi_before_mean", 0.0),
            "ndvi_after_mean": result.get("ndvi_after_mean", 0.0),
            "ndvi_diff_mean": result.get("ndvi_diff_mean", 0.0),
            "verified_area_ha": result.get("verified_area_ha", 0.0),
            "deforestation_mask_path": result.get("deforestation_mask_path"),
            "deforested_pixel_ratio": result.get("deforested_pixel_ratio")
        }
        return serializable_result


class ProtectedAreaLookupTool(BaseTool):
    name = "ProtectedAreaLookupTool"
    description = "Check if coordinates lie inside a legally protected area (national park, reserve)."

    def run(self, parameters: dict, db=None) -> any:
        lat = parameters.get("latitude")
        lon = parameters.get("longitude")
        logger.info(f"Running ProtectedAreaLookupTool for coordinates: ({lat}, {lon})")
        protected_info = check_intersection_with_protected_areas(lat, lon)
        return protected_info


class HistoricalAlertTool(BaseTool):
    name = "HistoricalAlertTool"
    description = "Checks recent proximity alerts (within 30 days) to detect active clearance clusters."

    def run(self, parameters: dict, db=None) -> any:
        lat = parameters.get("latitude")
        lon = parameters.get("longitude")
        alert_id = parameters.get("alert_id")
        logger.info(f"Running HistoricalAlertTool for alert {alert_id} at ({lat}, {lon})")
        if db is None:
            logger.warning("No DB session provided to HistoricalAlertTool. Returning 0.")
            return 0
            
        # Call contextual service lookup
        alert_temp = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert_temp:
            # Fallback mock alert object
            alert_temp = Alert(id=alert_id, latitude=lat, longitude=lon)
            
        enricher = ContextEnrichmentService()
        enrichment_data = enricher.enrich_alert_context(alert_temp, db)
        return enrichment_data


class ReportGeneratorTool(BaseTool):
    name = "ReportGeneratorTool"
    description = "Generates a comparison PNG matrix and compiles a professional PDF report."

    def run(self, parameters: dict, db=None) -> any:
        alert_id = parameters.get("alert_id")
        analysis_result = parameters.get("analysis_result")
        logger.info(f"Running ReportGeneratorTool for alert {alert_id}")
        
        if db is None:
            raise ValueError("Database session must be provided to ReportGeneratorTool")
            
        alert_db = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert_db:
            raise ValueError(f"Alert {alert_id} not found in database")
            
        # Generate comparison PNG
        alert_dir = Path(alert_db.imagery_before_path).parent.parent
        b_rgb = np.load(alert_db.imagery_before_path)
        a_rgb = np.load(alert_db.imagery_after_path)
        
        b_red = np.load(alert_dir / "before" / "red.npy")
        b_nir = np.load(alert_dir / "before" / "nir.npy")
        a_red = np.load(alert_dir / "after" / "red.npy")
        a_nir = np.load(alert_dir / "after" / "nir.npy")
        
        ndvi_before = calculate_ndvi(b_red, b_nir)
        ndvi_after = calculate_ndvi(a_red, a_nir)
        
        mask_path = alert_dir / "deforestation_mask.npy"
        if mask_path.exists():
            deforestation_mask = np.load(mask_path)
        else:
            # Fallback recalculate
            from backend.utils.ndvi import calculate_deforestation_mask
            deforestation_mask = calculate_deforestation_mask(ndvi_before, ndvi_after, 0.25)
            
        comp_img_path = str(alert_dir / "comparison.png")
        generate_comparison_image(
            before_rgb=b_rgb,
            after_rgb=a_rgb,
            before_ndvi=ndvi_before,
            after_ndvi=ndvi_after,
            deforestation_mask=deforestation_mask,
            save_path=comp_img_path
        )
        
        # Call report compiler service
        reporter = ReportGeneratorService()
        pdf_path = reporter.generate_pdf_report(alert_db, analysis_result, comp_img_path)
        return pdf_path


class NotificationTool(BaseTool):
    name = "NotificationTool"
    description = "Send the compiled PDF report via email notification to local authorities."

    def run(self, parameters: dict, db=None) -> any:
        recipient_email = parameters.get("recipient_email")
        alert_id = parameters.get("alert_id")
        pdf_path = parameters.get("pdf_path")
        logger.info(f"Running NotificationTool for alert {alert_id} -> {recipient_email}")
        notifier = NotificationService()
        sent = notifier.send_report_notification(recipient_email, alert_id, pdf_path)
        return sent


class DashboardTool(BaseTool):
    name = "DashboardTool"
    description = "Log activity/sync details to keep the dashboard timeline up to date."

    def run(self, parameters: dict, db=None) -> any:
        alert_id = parameters.get("alert_id")
        status = parameters.get("status")
        logger.info(f"Running DashboardTool sync for alert {alert_id} (status: {status})")
        return {"status": "success", "alert_id": alert_id, "synced_status": status}


class DatabaseTool(BaseTool):
    name = "DatabaseTool"
    description = "Performs read, write, check and update actions on SQLite entities."

    def run(self, parameters: dict, db=None) -> any:
        operation = parameters.get("operation")
        params = parameters.get("parameters", {})
        
        if db is None:
            raise ValueError("Database session (db) must be provided to DatabaseTool.")
            
        logger.info(f"Running DatabaseTool operation: {operation}")
            
        if operation == "check_exists":
            lat = params.get("latitude")
            lon = params.get("longitude")
            # Tolerance ~ 100 meters
            exists = db.query(Alert).filter(
                Alert.latitude.between(lat - 0.001, lat + 0.001),
                Alert.longitude.between(lon - 0.001, lon + 0.001),
                Alert.status != "False Positive"
            ).first()
            if exists:
                return {"exists": True, "alert_id": exists.id}
                
            # Cooldown logic: skip re-evaluating false positives within 24 hours
            from datetime import datetime, timedelta
            cooldown_limit = datetime.now() - timedelta(hours=24)
            recent_fp = db.query(Alert).filter(
                Alert.latitude.between(lat - 0.001, lat + 0.001),
                Alert.longitude.between(lon - 0.001, lon + 0.001),
                Alert.status == "False Positive",
                Alert.detected_at >= cooldown_limit
            ).first()
            if recent_fp:
                return {"exists": True, "alert_id": recent_fp.id}
                
            return {"exists": False}
            
        elif operation == "create_alert":
            from datetime import datetime
            from sqlalchemy import func
            lat = params.get("latitude")
            lon = params.get("longitude")
            area_ha = params.get("area_ha")
            details = params.get("details", "")
            region_name = params.get("region_name", "Amazon Wildlife Reserve")
            detected_at_str = params.get("detected_at")
            
            region = db.query(RegionOfInterest).filter(RegionOfInterest.name == region_name).first()
            region_id = region.id if region else None
            
            detected_at_val = None
            if detected_at_str:
                if isinstance(detected_at_str, str):
                    try:
                        if detected_at_str.endswith('Z'):
                            detected_at_str = detected_at_str[:-1]
                        detected_at_val = datetime.fromisoformat(detected_at_str)
                    except ValueError:
                        pass
            
            alert = Alert(
                region_id=region_id,
                latitude=lat,
                longitude=lon,
                area_ha=area_ha,
                status="Pending",
                details=details,
                detected_at=detected_at_val if detected_at_val else func.now()
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            return {"alert_id": alert.id, "status": alert.status}
            
        elif operation == "update_alert":
            alert_id = params.get("alert_id")
            status = params.get("status")
            risk_level = params.get("risk_level")
            details = params.get("details")
            ndvi_before = params.get("ndvi_before")
            ndvi_after = params.get("ndvi_after")
            ndvi_diff = params.get("ndvi_diff")
            imagery_before_path = params.get("imagery_before_path")
            imagery_after_path = params.get("imagery_after_path")
            
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return {"error": "Alert not found"}
                
            if status:
                alert.status = status
            if risk_level:
                alert.risk_level = risk_level
            if ndvi_before is not None:
                alert.ndvi_before = ndvi_before
            if ndvi_after is not None:
                alert.ndvi_after = ndvi_after
            if ndvi_diff is not None:
                alert.ndvi_diff = ndvi_diff
            if imagery_before_path:
                alert.imagery_before_path = imagery_before_path
            if imagery_after_path:
                alert.imagery_after_path = imagery_after_path
            if details:
                existing_details = json.loads(alert.details) if alert.details else {}
                if isinstance(details, dict):
                    existing_details.update(details)
                    alert.details = json.dumps(existing_details)
                elif isinstance(details, str):
                    try:
                        existing_details.update(json.loads(details))
                        alert.details = json.dumps(existing_details)
                    except:
                        alert.details = details
            db.commit()
            db.refresh(alert)
            return {"alert_id": alert.id, "status": alert.status, "risk_level": alert.risk_level}
            
        elif operation == "enrich_alert":
            alert_id = params.get("alert_id")
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return {"error": "Alert not found"}
                
            existing_details = json.loads(alert.details) if alert.details else {}
            existing_details.update({
                "protected_info": {
                    "is_protected": params.get("is_protected", False),
                    "name": params.get("protected_area_name"),
                    "category": params.get("protected_area_category")
                },
                "spatial_cluster": {
                    "neighboring_alerts_30d": params.get("neighboring_alerts_30d", 0),
                    "is_active_cluster": params.get("is_active_cluster", False)
                }
            })
            alert.details = json.dumps(existing_details)
            db.commit()
            return {"status": "success", "alert_id": alert.id}

        elif operation == "create_report":
            alert_id = params.get("alert_id")
            file_path = params.get("file_path")
            narrative_summary = params.get("narrative_summary")
            recommended_action = params.get("recommended_action")
            recipient_email = params.get("recipient_email")
            status = params.get("status", "Pending")
            
            report = Report(
                alert_id=alert_id,
                file_path=file_path,
                narrative_summary=narrative_summary,
                recommended_action=recommended_action,
                recipient_email=recipient_email,
                status=status
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return {"report_id": report.id, "status": report.status}
            
        elif operation == "update_report":
            report_id = params.get("report_id")
            status = params.get("status")
            
            report = db.query(Report).filter(Report.id == report_id).first()
            if not report:
                return {"error": "Report not found"}
                
            report.status = status
            db.commit()
            db.refresh(report)
            return {"report_id": report.id, "status": report.status}
            
        else:
            return {"error": f"Unknown database operation: {operation}"}
