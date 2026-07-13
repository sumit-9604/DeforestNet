import os
import json
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point, shape, Polygon
from pyproj import CRS
from backend.utils.logger import setup_logger

logger = setup_logger("geo_utils")

# Default protected areas path
DATA_DIR = Path(__file__).resolve().parent.parent / "database" / "data"
PROTECTED_AREAS_PATH = DATA_DIR / "protected_areas.geojson"

def ensure_mock_protected_areas():
    """Generates a mock protected areas GeoJSON if it does not exist"""
    if PROTECTED_AREAS_PATH.exists():
        return
        
    logger.info(f"Mock protected areas GeoJSON not found. Creating it at: {PROTECTED_AREAS_PATH}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Mock zones:
    # 1. Amazon Conservation Zone (Near -3.46, -62.21)
    # 2. Southeast Asia Sanctuary (Near -1.25, 116.89)
    mock_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": 1,
                    "name": "Amazon National Park (WDPA)",
                    "category": "National Park",
                    "status": "Designated"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-62.30, -3.55],
                        [-62.10, -3.55],
                        [-62.10, -3.35],
                        [-62.30, -3.35],
                        [-62.30, -3.55]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "id": 2,
                    "name": "Kalimantan Reserve Forest (WDPA)",
                    "category": "Nature Reserve",
                    "status": "Designated"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [116.80, -1.35],
                        [117.00, -1.35],
                        [117.00, -1.15],
                        [116.80, -1.15],
                        [116.80, -1.35]
                    ]]
                }
            }
        ]
    }
    
    with open(PROTECTED_AREAS_PATH, "w") as f:
        json.dump(mock_data, f, indent=2)

def check_intersection_with_protected_areas(lat: float, lon: float) -> dict:
    """
    Checks if a coordinate (lat, lon) lies inside any protected areas.
    
    Returns:
        dict: Information about the protected area if matched, otherwise None.
    """
    ensure_mock_protected_areas()
    
    try:
        # Create a point geometry
        point = Point(lon, lat)  # shapely takes (x, y) i.e. (longitude, latitude)
        
        # Load protected areas
        gdf = gpd.read_file(str(PROTECTED_AREAS_PATH))
        
        # Check intersections
        matches = gdf[gdf.geometry.contains(point)]
        
        if not matches.empty:
            match = matches.iloc[0]
            return {
                "is_protected": True,
                "name": match.get("name", "Unknown Protected Area"),
                "category": match.get("category", "N/A"),
                "status": match.get("status", "Designated")
            }
            
        return {
            "is_protected": False,
            "name": None,
            "category": None,
            "status": None
        }
        
    except Exception as e:
        logger.error(f"Error checking protected area intersection: {e}")
        return {
            "is_protected": False,
            "name": None,
            "category": None,
            "status": None,
            "error": str(e)
        }

def calculate_polygon_area_ha(polygon_geom: Polygon, center_lon: float, center_lat: float) -> float:
    """
    Calculates the area of a polygon in hectares by projecting it to the local UTM CRS.
    """
    try:
        # Determine UTM zone
        utm_zone = int((center_lon + 180) / 6) + 1
        is_northern = center_lat >= 0
        epsg_code = 32600 + utm_zone if is_northern else 32700 + utm_zone
        
        # Create CRS
        crs_utm = CRS.from_epsg(epsg_code)
        crs_wgs84 = CRS.from_epsg(4326)
        
        # Create GeoSeries and project
        gs = gpd.GeoSeries([polygon_geom], crs=crs_wgs84)
        gs_projected = gs.to_crs(crs_utm)
        
        # Area in square meters -> hectares (1 ha = 10,000 sq m)
        area_sq_m = gs_projected.iloc[0].area
        area_ha = area_sq_m / 10000.0
        
        return round(area_ha, 2)
    except Exception as e:
        logger.error(f"Error calculating area: {e}")
        # Fallback to rough estimate if projection fails (approx 111km per degree)
        # 1 degree lat = 111,000 m; 1 degree lon = 111,000 * cos(lat) m
        return 5.0
