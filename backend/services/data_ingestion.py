import os
import json
import math
import random
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from backend.config import (
    SIMULATION_MODE,
    SENTINEL_HUB_CLIENT_ID,
    SENTINEL_HUB_CLIENT_SECRET,
    PLANET_API_KEY,
    IMAGERY_DIR
)
from backend.utils.logger import setup_logger

logger = setup_logger("data_ingestion")

# Each GFW integrated alert pixel represents a 10m x 10m ground cell = 0.01 hectares
PIXEL_AREA_HA = 0.01
# Pixels within this distance (meters) are considered part of the same clearing event
CLUSTER_DISTANCE_THRESHOLD_M = 25


class DataIngestionService:
    def __init__(self):
        self.simulation = SIMULATION_MODE

    @staticmethod
    def _haversine_distance_m(lat1, lon1, lat2, lon2):

        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))

    def _cluster_pixels(self, pixels, distance_threshold_m=CLUSTER_DISTANCE_THRESHOLD_M):
        """
        Groups nearby alert pixels into clusters using simple BFS distance-based grouping.
        Returns a list of clusters, where each cluster is a list of pixel indices.
        """
        n = len(pixels)
        visited = [False] * n
        clusters = []

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            queue = [i]
            cluster_idx = [i]

            while queue:
                current = queue.pop()
                for j in range(n):
                    if visited[j]:
                        continue
                    dist = self._haversine_distance_m(
                        pixels[current]["latitude"], pixels[current]["longitude"],
                        pixels[j]["latitude"], pixels[j]["longitude"]
                    )
                    if dist <= distance_threshold_m:
                        visited[j] = True
                        queue.append(j)
                        cluster_idx.append(j)

            clusters.append(cluster_idx)

        return clusters

    def _build_clustered_alerts(self, pixels):

        if not pixels:
            return []

        clusters = self._cluster_pixels(pixels)
        alerts = []

        for cluster_idx in clusters:
            cluster_pixels = [pixels[i] for i in cluster_idx]

            lats = [p["latitude"] for p in cluster_pixels]
            lons = [p["longitude"] for p in cluster_pixels]
            centroid_lat = sum(lats) / len(lats)
            centroid_lon = sum(lons) / len(lons)

            pixel_count = len(cluster_pixels)
            area_ha = round(pixel_count * PIXEL_AREA_HA, 2)

            confidences = [p.get("confidence", "nominal") for p in cluster_pixels]
            confidence = "high" if "high" in confidences else "nominal"

            dates = [p.get("date") for p in cluster_pixels if p.get("date")]
            latest_date = max(dates) if dates else datetime.utcnow().isoformat() + "Z"

            alerts.append({
                "latitude": centroid_lat,
                "longitude": centroid_lon,
                "area_ha": area_ha,
                "confidence": confidence,
                "detected_at": latest_date,
                "details": json.dumps({
                    "source": "GFW Integrated Alerts",
                    "pixel_count": pixel_count,
                    "cluster_radius_m": CLUSTER_DISTANCE_THRESHOLD_M
                })
            })

        return alerts

    def fetch_deforestation_alerts(self, region_name: str = "Amazon Wildlife Reserve") -> list:
        """
        Fetches deforestation alert coordinates from GFW (Global Forest Watch) API
        or generates mock alerts in simulation mode.
        """
        if self.simulation:
            logger.info(f"[Simulation] Generating mock deforestation alerts for region: {region_name}")

            if "Amazon" in region_name:
                center_lat, center_lon = -3.46, -62.21
            elif "Kalimantan" in region_name or "Southeast Asia" in region_name:
                center_lat, center_lon = -1.25, 116.89
            else:
                center_lat, center_lon = -3.46, -62.21  # Default to Amazon area

            alerts = []
            num_alerts = random.randint(1, 3)
            for i in range(num_alerts):
                lat = center_lat + random.uniform(-0.05, 0.05)
                lon = center_lon + random.uniform(-0.05, 0.05)
                area = round(random.uniform(1.5, 12.0), 2)
                confidence = random.choice(["high", "nominal"])

                alerts.append({
                    "latitude": lat,
                    "longitude": lon,
                    "area_ha": area,
                    "confidence": confidence,
                    "detected_at": (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat() + "Z",
                    "details": json.dumps({
                        "satellite": "Sentinel-2",
                        "cloud_cover_percent": round(random.uniform(0.0, 15.0), 1),
                        "sensor": "MSI"
                    })
                })
            return alerts

        else:
            # Real API call to Global Forest Watch API (Integrated Alerts, raster dataset)
            logger.info(f"Querying GFW Integrated Alerts API for region: {region_name}")
            try:
                import requests

                api_key = os.getenv("GFW_API_KEY", "")
                if not api_key:
                    raise ValueError("GFW_API_KEY is not configured. Falling back to simulation.")

                # Region geometry (bounding box polygon) — matches ROIs used elsewhere
                if "Amazon" in region_name:
                    geometry = {
                        "type": "Polygon",
                        "coordinates": [[
                            [-62.3, -3.55], [-62.1, -3.55],
                            [-62.1, -3.35], [-62.3, -3.35],
                            [-62.3, -3.55]
                        ]]
                    }
                elif "Kalimantan" in region_name or "Southeast Asia" in region_name:
                    geometry = {
                        "type": "Polygon",
                        "coordinates": [[
                            [116.8, -1.35], [117.0, -1.35],
                            [117.0, -1.15], [116.8, -1.15],
                            [116.8, -1.35]
                        ]]
                    }
                else:
                    geometry = {
                        "type": "Polygon",
                        "coordinates": [[
                            [-62.3, -3.55], [-62.1, -3.55],
                            [-62.1, -3.35], [-62.3, -3.35],
                            [-62.3, -3.55]
                        ]]
                    }

                headers = {
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                }

                # Note: correct endpoint requires /json suffix, uses "results" table, not "data"
                url = "https://data-api.globalforestwatch.org/dataset/gfw_integrated_alerts/latest/query/json"
                payload = {
                    "sql": (
                        "SELECT longitude, latitude, gfw_integrated_alerts__date, "
                        "gfw_integrated_alerts__intensity, gfw_integrated_alerts__confidence "
                        "FROM results WHERE gfw_integrated_alerts__date >= '2026-06-01' AND gfw_integrated_alerts__confidence = 'high'"
                    ),
                    "geometry": geometry
                }

                response = requests.post(url, json=payload, headers=headers, timeout=15)

                if response.status_code == 200:
                    raw_data = response.json().get("data", [])

                    # Normalize raw GFW pixel records into a simple shape for clustering
                    pixels = [
                        {
                            "latitude": item["latitude"],
                            "longitude": item["longitude"],
                            "confidence": item.get("gfw_integrated_alerts__confidence", "nominal"),
                            "date": item.get("gfw_integrated_alerts__date")
                        }
                        for item in raw_data
                    ]

                    logger.info(f"Retrieved {len(pixels)} raw alert pixels from GFW for {region_name}. Clustering into events...")

                    # Group nearby 10m pixels into real clearing events with real area
                    alerts = self._build_clustered_alerts(pixels)

                    logger.info(f"Clustered into {len(alerts)} deforestation events for {region_name}")
                    return alerts
                else:
                    raise ValueError(f"GFW API returned status {response.status_code}: {response.text}")

            except Exception as e:
                logger.warning(f"Failed to query GFW API: {e}. Falling back to simulation alerts.")

            self.simulation = True
            return self.fetch_deforestation_alerts(region_name)

    def fetch_satellite_imagery(self, lat: float, lon: float, alert_id: int) -> dict:
        """
        Retrieves "before" and "after" satellite imagery bands (Red, NIR, and RGB) for the coordinates.
        In simulation mode, creates mock matrices and saves them as files.
        """
        before_dir = IMAGERY_DIR / f"alert_{alert_id}" / "before"
        after_dir = IMAGERY_DIR / f"alert_{alert_id}" / "after"
        before_dir.mkdir(parents=True, exist_ok=True)
        after_dir.mkdir(parents=True, exist_ok=True)

        if self.simulation:
            return self.fetch_satellite_imagery_mock(lat, lon, alert_id)
        else:
            logger.info(f"Querying Sentinel Hub API for coordinates: ({lat}, {lon})")
            if not SENTINEL_HUB_CLIENT_ID or not SENTINEL_HUB_CLIENT_SECRET:
                logger.warning("Sentinel Hub API credentials missing. Falling back to Simulation Mode.")
                return self.fetch_satellite_imagery_mock(lat, lon, alert_id)

            try:
                # 1. Fetch Alert Date from Database to establish context windows
                from backend.database.database import SessionLocal
                from backend.models.alert import Alert

                db = SessionLocal()
                detected_at = None
                try:
                    alert = db.query(Alert).filter(Alert.id == alert_id).first()
                    if alert:
                        detected_at = alert.detected_at
                finally:
                    db.close()

                if not detected_at:
                    detected_at = datetime.utcnow()

                # 2. Define before and after date ranges
                before_from = (detected_at - timedelta(days=45)).strftime("%Y-%m-%dT00:00:00Z")
                before_to = (detected_at - timedelta(days=15)).strftime("%Y-%m-%dT23:59:59Z")
                after_from = detected_at.strftime("%Y-%m-%dT00:00:00Z")
                after_to = (detected_at + timedelta(days=15)).strftime("%Y-%m-%dT23:59:59Z")

                logger.info("Fetching BEFORE imagery from Sentinel Hub...")
                before_red, before_nir, before_green, before_blue = self._query_sentinel_hub(
                    lat, lon, before_from, before_to
                )

                logger.info("Fetching AFTER imagery from Sentinel Hub...")
                after_red, after_nir, after_green, after_blue = self._query_sentinel_hub(
                    lat, lon, after_from, after_to
                )

                # Save before bands
                np.save(before_dir / "red.npy", before_red)
                np.save(before_dir / "nir.npy", before_nir)
                before_rgb = np.stack([before_blue, before_green, before_red], axis=-1)
                np.save(before_dir / "rgb.npy", before_rgb)

                # Save after bands
                np.save(after_dir / "red.npy", after_red)
                np.save(after_dir / "nir.npy", after_nir)
                after_rgb = np.stack([after_blue, after_green, after_red], axis=-1)
                np.save(after_dir / "rgb.npy", after_rgb)

                return {
                    "before": {
                        "red": str(before_dir / "red.npy"),
                        "nir": str(before_dir / "nir.npy"),
                        "rgb": str(before_dir / "rgb.npy")
                    },
                    "after": {
                        "red": str(after_dir / "red.npy"),
                        "nir": str(after_dir / "nir.npy"),
                        "rgb": str(after_dir / "rgb.npy")
                    }
                }

            except Exception as e:
                logger.error(f"Error calling Sentinel Hub API: {e}. Falling back to simulation.", exc_info=True)
                return self.fetch_satellite_imagery_mock(lat, lon, alert_id)

    def fetch_satellite_imagery_mock(self, lat: float, lon: float, alert_id: int) -> dict:
        """Helper to generate mock satellite imagery files for simulation mode"""
        before_dir = IMAGERY_DIR / f"alert_{alert_id}" / "before"
        after_dir = IMAGERY_DIR / f"alert_{alert_id}" / "after"
        before_dir.mkdir(parents=True, exist_ok=True)
        after_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[Simulation] Generating mock satellite imagery bands for alert {alert_id} at ({lat}, {lon})")
        height, width = 200, 200

        before_red = np.random.normal(0.08, 0.02, (height, width))
        before_nir = np.random.normal(0.75, 0.05, (height, width))
        before_green = np.random.normal(0.35, 0.03, (height, width))
        before_blue = np.random.normal(0.06, 0.01, (height, width))

        # Clip bands to valid reflectance [0, 1.0]
        before_red = np.clip(before_red, 0, 1.0)
        before_nir = np.clip(before_nir, 0, 1.0)
        before_green = np.clip(before_green, 0, 1.0)
        before_blue = np.clip(before_blue, 0, 1.0)

        # Save before bands as numpy arrays
        np.save(before_dir / "red.npy", before_red)
        np.save(before_dir / "nir.npy", before_nir)
        before_rgb = np.stack([before_blue, before_green, before_red], axis=-1)  # BGR for OpenCV
        np.save(before_dir / "rgb.npy", before_rgb)

        after_red = before_red.copy()
        after_nir = before_nir.copy()
        after_green = before_green.copy()
        after_blue = before_blue.copy()

        # Deforestation patch: high Red, low NIR
        start_y, end_y = 60, 140
        start_x, end_x = 70, 130

        after_red[start_y:end_y, start_x:end_x] = np.random.normal(0.38, 0.03, (end_y - start_y, end_x - start_x))
        after_nir[start_y:end_y, start_x:end_x] = np.random.normal(0.16, 0.02, (end_y - start_y, end_x - start_x))
        after_green[start_y:end_y, start_x:end_x] = np.random.normal(0.18, 0.02, (end_y - start_y, end_x - start_x))
        after_blue[start_y:end_y, start_x:end_x] = np.random.normal(0.14, 0.02, (end_y - start_y, end_x - start_x))

        # Add logging trails
        for i in range(200):
            if 20 <= i <= 180:
                road_width = 3
                after_red[i, max(0, i - road_width):min(199, i + road_width)] = 0.35
                after_nir[i, max(0, i - road_width):min(199, i + road_width)] = 0.18
                after_green[i, max(0, i - road_width):min(199, i + road_width)] = 0.20
                after_blue[i, max(0, i - road_width):min(199, i + road_width)] = 0.13

        # Clip bands
        after_red = np.clip(after_red, 0, 1.0)
        after_nir = np.clip(after_nir, 0, 1.0)
        after_green = np.clip(after_green, 0, 1.0)
        after_blue = np.clip(after_blue, 0, 1.0)

        # Save after bands
        np.save(after_dir / "red.npy", after_red)
        np.save(after_dir / "nir.npy", after_nir)
        after_rgb = np.stack([after_blue, after_green, after_red], axis=-1)  # BGR
        np.save(after_dir / "rgb.npy", after_rgb)

        return {
            "before": {
                "red": str(before_dir / "red.npy"),
                "nir": str(before_dir / "nir.npy"),
                "rgb": str(before_dir / "rgb.npy")
            },
            "after": {
                "red": str(after_dir / "red.npy"),
                "nir": str(after_dir / "nir.npy"),
                "rgb": str(after_dir / "rgb.npy")
            }
        }

    def _query_sentinel_hub(self, lat: float, lon: float, from_date: str, to_date: str) -> tuple:
        """
        Queries Sentinel Hub Process API for the given coordinates and date range.
        Returns:
            (red_band, nir_band, green_band, blue_band) as numpy arrays.
        """
        import requests

        # 1. Fetch OAuth2 Token
        token_url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': SENTINEL_HUB_CLIENT_ID,
            'client_secret': SENTINEL_HUB_CLIENT_SECRET
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        token_res = requests.post(token_url, data=payload, headers=headers, timeout=10)
        token_res.raise_for_status()
        access_token = token_res.json()['access_token']

        # 2. Setup BBOX (approx. 600m x 600m)
        lat_delta = 0.003
        lon_delta = 0.003 / math.cos(math.radians(lat))
        bbox = [lon - lon_delta, lat - lat_delta, lon + lon_delta, lat + lat_delta]

        # 3. Setup Process request
        process_url = "https://services.sentinel-hub.com/api/v1/process"
        
        evalscript = """
        //VERSION=3
        function setup() {
          return {
            input: ["B04", "B08", "B03", "B02"],
            output: { bands: 4, sampleType: "FLOAT32" }
          };
        }
        function evaluatePixel(sample) {
          return [sample.B04, sample.B08, sample.B03, sample.B02];
        }
        """

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "image/tiff"
        }

        process_payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": from_date,
                                "to": to_date
                            },
                            "mosaickingOrder": "leastRecent"
                        }
                    }
                ]
            },
            "output": {
                "width": 200,
                "height": 200,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            },
            "evalscript": evalscript
        }

        response = requests.post(process_url, json=process_payload, headers=headers, timeout=30)
        response.raise_for_status()

        # 4. Parse TIFF
        import io
        import rasterio
        with rasterio.open(io.BytesIO(response.content)) as src:
            data = src.read()
            red = np.clip(data[0], 0, 1.0)
            nir = np.clip(data[1], 0, 1.0)
            green = np.clip(data[2], 0, 1.0)
            blue = np.clip(data[3], 0, 1.0)
            
            return red, nir, green, blue