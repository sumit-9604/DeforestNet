from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List

from backend.database.database import get_db
from backend.models.alert import Alert
from backend.models.report import Report
from backend.utils.logger import setup_logger

logger = setup_logger("api_dashboard")
router = APIRouter()

@router.get("/stats")
def get_dashboard_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns aggregated metrics for the dashboard:
    - Total alerts processed
    - Total verified forest loss area (hectares)
    - Active Critical & High alerts count
    - Alert counts grouped by status and risk level
    """
    # 1. Total counts
    total_alerts = db.query(Alert).count()
    
    # 2. Count by status
    status_counts = db.query(
        Alert.status, func.count(Alert.id)
    ).group_by(Alert.status).all()
    
    status_map = {status: count for status, count in status_counts}
    
    # 3. Count by risk
    risk_counts = db.query(
        Alert.risk_level, func.count(Alert.id)
    ).filter(Alert.risk_level.isnot(None)).group_by(Alert.risk_level).all()
    
    risk_map = {risk: count for risk, count in risk_counts}
    
    # 4. Total area lost (only sum for Verified and Reported alerts)
    area_sum = db.query(func.sum(Alert.area_ha)).filter(
        Alert.status.in_(["Verified", "Reported"])
    ).scalar() or 0.0
    
    # 5. Critical counts
    critical_alerts = db.query(Alert).filter(Alert.risk_level == "Critical").count()
    high_alerts = db.query(Alert).filter(Alert.risk_level == "High").count()
    
    return {
        "metrics": {
            "total_alerts": total_alerts,
            "verified_area_lost_ha": round(area_sum, 2),
            "critical_risk_alerts": critical_alerts,
            "high_risk_alerts": high_alerts,
            "pending_review": status_map.get("Pending", 0),
            "resolved_reports": status_map.get("Reported", 0)
        },
        "by_status": {
            "Pending": status_map.get("Pending", 0),
            "Verified": status_map.get("Verified", 0),
            "False Positive": status_map.get("False Positive", 0),
            "Reported": status_map.get("Reported", 0),
        },
        "by_risk": {
            "Critical": risk_map.get("Critical", 0),
            "High": risk_map.get("High", 0),
            "Medium": risk_map.get("Medium", 0),
            "Low": risk_map.get("Low", 0),
        }
    }

@router.get("/recent-activity")
def get_recent_activity_timeline(limit: int = 10, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns a unified timeline feed of recent system events:
    - New alerts detected
    - Reports compiled and sent
    - Reviews completed
    """
    timeline = []
    
    # Fetch recent alerts
    recent_alerts = db.query(Alert).order_by(Alert.detected_at.desc()).limit(limit).all()
    for alert in recent_alerts:
        timeline.append({
            "id": f"event_alert_{alert.id}",
            "type": "alert_detected",
            "message": f"Deforestation alert ({alert.area_ha:.1f} ha) detected at coordinate ({alert.latitude:.4f}, {alert.longitude:.4f}).",
            "timestamp": alert.detected_at.isoformat(),
            "status": alert.status,
            "severity": alert.risk_level or "Unknown"
        })
        
    # Fetch recent reports
    recent_reports = db.query(Report).order_by(Report.generated_at.desc()).limit(limit).all()
    for report in recent_reports:
        timeline.append({
            "id": f"event_report_{report.id}",
            "type": "report_dispatched",
            "message": f"Evidence report successfully compiled and sent to {report.recipient_email}.",
            "timestamp": report.generated_at.isoformat(),
            "status": report.status,
            "severity": "Info"
        })
        
    # Sort unified timeline chronologically (newest first)
    timeline.sort(key=lambda x: x["timestamp"], reverse=True)
    return timeline[:limit]
