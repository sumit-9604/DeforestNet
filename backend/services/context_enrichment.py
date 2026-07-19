import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import and_
from datetime import datetime, timedelta
from backend.utils.geo_utils import check_intersection_with_protected_areas
from backend.models.alert import Alert
from backend.utils.logger import setup_logger

logger = setup_logger("context_enrichment")

class ContextEnrichmentService:
    def enrich_alert_context(self, alert_db_model: Alert, db) -> dict:
        """
        Enriches the alert with geographic and historical database context:
        - Checks protected area intersection.
        - Checks for historical alerts nearby to find active clusters.
        
        Args:
            alert_db_model (Alert): The Alert database object.
            db: SQLAlchemy Session.
            
        Returns:
            dict: Enriched attributes.
        """
        lat = alert_db_model.latitude
        lon = alert_db_model.longitude
        
        logger.info(f"Enriching context for alert {alert_db_model.id} at ({lat}, {lon})")
        
        # 1. Protected Areas check
        protected_info = check_intersection_with_protected_areas(lat, lon)
        
        # 2. Historical proximity check (spatial clustering in last 30 days)
        # 1km is roughly 0.009 degrees latitude. Longitude depends on latitude, but
        # 0.01 degrees is a standard bounding box approximation for proximity queries.
        lat_tolerance = 0.01
        lon_tolerance = 0.01
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        try:
            # Find neighboring alerts in the database
            neighbors = db.query(Alert).filter(
                and_(
                    Alert.id != alert_db_model.id,
                    Alert.latitude.between(lat - lat_tolerance, lat + lat_tolerance),
                    Alert.longitude.between(lon - lon_tolerance, lon + lon_tolerance),
                    Alert.detected_at >= thirty_days_ago
                )
            ).all()
            
            neighbor_count = len(neighbors)
            logger.info(f"Found {neighbor_count} neighboring alerts within 1km in the last 30 days.")
            
        except Exception as e:
            logger.error(f"Error querying historical neighborhood alerts: {e}")
            neighbor_count = 0
            
        enrichment_data = {
            "is_protected": protected_info.get("is_protected", False),
            "protected_area_name": protected_info.get("name"),
            "protected_area_category": protected_info.get("category"),
            "protected_area_status": protected_info.get("status"),
            "neighboring_alerts_30d": neighbor_count,
            "is_active_cluster": neighbor_count >= 2  # 2 or more nearby alerts indicates active logging patterns
        }
        
        return enrichment_data
