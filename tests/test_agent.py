import pytest
from unittest.mock import patch
from backend.agent.agent import ForestGuardAgent
from backend.models.alert import Alert, RegionOfInterest
from backend.models.report import Report

def test_agent_run(db_session):
    # Setup mock deterministic alerts
    mock_alerts = [{
        "latitude": -3.46,
        "longitude": -62.21,
        "area_ha": 5.5,
        "confidence": "high",
        "detected_at": "2026-07-20T12:00:00Z",
        "details": '{"satellite": "Sentinel-2"}'
    }]
    
    with patch("backend.services.data_ingestion.DataIngestionService.fetch_deforestation_alerts", return_value=mock_alerts):
        agent = ForestGuardAgent()
        
        # Run agent on the seeded Amazon Wildlife Reserve
        metrics = agent.run("Amazon Wildlife Reserve", db_session)
        
        # Assert that metrics are returned and contain expected values
        assert "raw_alerts_received" in metrics
        assert metrics["raw_alerts_received"] == 1
        assert metrics["new_alerts_processed"] == 1
        assert metrics["verified_deforestation_events"] == 1
        assert metrics["evidence_reports_dispatched"] == 1
        
        # Check that alerts were actually created in the DB
        alerts = db_session.query(Alert).all()
        assert len(alerts) > 0
        
        # Check that at least one report was compiled
        reports = db_session.query(Report).all()
        assert len(reports) > 0
        
        # Verify report fields
        report = reports[0]
        assert report.alert_id is not None
        assert report.file_path is not None
        assert report.recipient_email is not None
        
        # Run agent again; it should identify the existing alert as duplicate and skip it
        metrics_duplicate = agent.run("Amazon Wildlife Reserve", db_session)
        assert metrics_duplicate["new_alerts_processed"] == 0
