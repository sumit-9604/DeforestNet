import pytest
import numpy as np
import os
import json
from pathlib import Path
from backend.services.data_ingestion import DataIngestionService
from backend.services.change_detection import ChangeDetectionService
from backend.services.context_enrichment import ContextEnrichmentService
from backend.services.llm_reasoning import LLMReasoningService
from backend.models.alert import Alert

def test_haversine_distance():
    service = DataIngestionService()
    # Test identical coordinates
    dist = service._haversine_distance_m(0.0, 0.0, 0.0, 0.0)
    assert dist == 0.0
    
    # Distance between points
    dist = service._haversine_distance_m(0.0, 0.0, 1.0, 0.0)
    # Approx 111.1 km
    assert abs(dist - 111195.0) < 100.0

def test_pixel_clustering():
    service = DataIngestionService()
    # Coordinates within CLUSTER_DISTANCE_THRESHOLD_M (25 meters)
    # 0.0001 deg lat is approx 11 meters
    pixels = [
        {"latitude": 0.0, "longitude": 0.0, "confidence": "high", "date": "2026-07-20"},
        {"latitude": 0.0001, "longitude": 0.0, "confidence": "nominal", "date": "2026-07-19"},
        # Far away point
        {"latitude": 1.0, "longitude": 1.0, "confidence": "nominal", "date": "2026-07-18"}
    ]
    clusters = service._cluster_pixels(pixels)
    # Should have two clusters: [0, 1] and [2]
    assert len(clusters) == 2
    assert 0 in clusters[0] and 1 in clusters[0]
    assert 2 in clusters[1]

def test_fetch_deforestation_alerts():
    service = DataIngestionService()
    service.simulation = True
    alerts = service.fetch_deforestation_alerts("Amazon Wildlife Reserve")
    assert len(alerts) >= 1
    for alert in alerts:
        assert "latitude" in alert
        assert "longitude" in alert
        assert "area_ha" in alert
        assert "confidence" in alert
        assert "detected_at" in alert

def test_change_detection(tmp_path):
    # Setup mock image paths
    before_red = tmp_path / "before_red.npy"
    before_nir = tmp_path / "before_nir.npy"
    after_red = tmp_path / "after_red.npy"
    after_nir = tmp_path / "after_nir.npy"
    
    # 10x10 images
    # Before: High greenness (Red low, NIR high) -> High NDVI
    # After: Deforested (Red high, NIR low) -> Low NDVI
    b_red_data = np.full((10, 10), 0.1, dtype=np.float32)
    b_nir_data = np.full((10, 10), 0.8, dtype=np.float32)
    a_red_data = np.full((10, 10), 0.5, dtype=np.float32)
    a_nir_data = np.full((10, 10), 0.2, dtype=np.float32)
    
    np.save(before_red, b_red_data)
    np.save(before_nir, b_nir_data)
    np.save(after_red, a_red_data)
    np.save(after_nir, a_nir_data)
    
    paths = {
        "before": {"red": str(before_red), "nir": str(before_nir)},
        "after": {"red": str(after_red), "nir": str(after_nir)}
    }
    
    detector = ChangeDetectionService(threshold=0.25)
    results = detector.detect_changes(paths, raw_alert_area=5.0)
    
    assert results["is_verified"] is True
    assert results["ndvi_before_mean"] > 0.7
    assert results["ndvi_after_mean"] < 0.0
    assert results["ndvi_diff_mean"] > 0.5
    assert results["verified_area_ha"] > 0.0

def test_context_enrichment(db_session):
    enricher = ContextEnrichmentService()
    
    # Test point inside mock Amazon Conservation Zone (-3.46, -62.21)
    alert = Alert(
        latitude=-3.46,
        longitude=-62.21,
        area_ha=5.0,
        status="Pending",
        detected_at=None
    )
    db_session.add(alert)
    db_session.commit()
    
    enriched = enricher.enrich_alert_context(alert, db_session)
    assert enriched["is_protected"] is True
    assert "Amazon" in enriched["protected_area_name"]
    
    # Check that neighbor count works (we have no neighbors yet)
    assert enriched["neighboring_alerts_30d"] == 0
    assert enriched["is_active_cluster"] is False
    
    # Now let's add neighbors
    n1 = Alert(latitude=-3.461, longitude=-62.211, area_ha=1.0, status="Pending")
    n2 = Alert(latitude=-3.459, longitude=-62.209, area_ha=2.0, status="Pending")
    db_session.add(n1)
    db_session.add(n2)
    db_session.commit()
    
    enriched = enricher.enrich_alert_context(alert, db_session)
    # The two neighbors are within 1km
    assert enriched["neighboring_alerts_30d"] == 2
    assert enriched["is_active_cluster"] is True

def test_llm_reasoning_fallback():
    reasoning = LLMReasoningService()
    # Force use of rule-based fallback
    reasoning.provider = "mock"
    
    # Test critical alert data
    data_critical = {
        "latitude": -3.46,
        "longitude": -62.21,
        "area_ha": 10.0,
        "ndvi_before_mean": 0.8,
        "ndvi_after_mean": 0.2,
        "ndvi_diff_mean": 0.6,
        "is_protected": True,
        "protected_area_name": "Amazon National Park (WDPA)",
        "protected_area_category": "National Park",
        "neighboring_alerts_30d": 3,
        "is_active_cluster": True
    }
    
    res = reasoning.analyze_alert(data_critical)
    assert res["risk_level"] == "Critical"
    assert "Dispatch an enforcement patrol immediately" in res["recommended_action"]
    
    # Test low alert data
    data_low = {
        "latitude": 0.0,
        "longitude": 0.0,
        "area_ha": 0.5,
        "ndvi_before_mean": 0.4,
        "ndvi_after_mean": 0.35,
        "ndvi_diff_mean": 0.05,
        "is_protected": False,
        "protected_area_name": None,
        "protected_area_category": None,
        "neighboring_alerts_30d": 0,
        "is_active_cluster": False
    }
    res_low = reasoning.analyze_alert(data_low)
    assert res_low["risk_level"] == "Low"
    assert "Flag for passive monitoring" in res_low["recommended_action"]
