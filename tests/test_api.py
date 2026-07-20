import pytest
import os
from backend.models.alert import Alert
from backend.models.report import Report

def test_api_trigger_check(client):
    # Trigger the agentic pipeline for a region
    response = client.post("/api/alerts/trigger-check?region_name=Amazon+Wildlife+Reserve")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Success"
    assert data["region"] == "Amazon Wildlife Reserve"
    assert data["raw_alerts_received"] > 0

def test_api_get_alerts(client):
    # Trigger first to populate alerts
    client.post("/api/alerts/trigger-check?region_name=Amazon+Wildlife+Reserve")
    
    # Retrieve all alerts
    response = client.get("/api/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "latitude" in data[0]
    assert "status" in data[0]
    
    # Retrieve specific alert by ID
    alert_id = data[0]["id"]
    response_detail = client.get(f"/api/alerts/{alert_id}")
    assert response_detail.status_code == 200
    assert response_detail.json()["id"] == alert_id

def test_api_update_alert_status(client):
    # Trigger first to populate alerts
    client.post("/api/alerts/trigger-check?region_name=Amazon+Wildlife+Reserve")
    
    response = client.get("/api/alerts/")
    alert = response.json()[0]
    alert_id = alert["id"]
    
    # Manually update status to Verified
    response_update = client.put(f"/api/alerts/{alert_id}", json={
        "status": "Verified",
        "risk_level": "High"
    })
    assert response_update.status_code == 200
    updated_data = response_update.json()
    assert updated_data["status"] == "Verified"
    assert updated_data["risk_level"] == "High"

def test_api_dashboard_endpoints(client):
    # Trigger first to populate data
    client.post("/api/alerts/trigger-check?region_name=Amazon+Wildlife+Reserve")
    
    # Check stats endpoint
    response_stats = client.get("/api/dashboard/stats")
    assert response_stats.status_code == 200
    data = response_stats.json()
    assert "metrics" in data
    assert "by_status" in data
    assert "by_risk" in data
    assert data["metrics"]["total_alerts"] > 0
    
    # Check recent activity timeline
    response_timeline = client.get("/api/dashboard/recent-activity")
    assert response_timeline.status_code == 200
    timeline = response_timeline.json()
    assert len(timeline) > 0
    assert any(item["type"] == "alert_detected" for item in timeline)

def test_api_reports_endpoints(client):
    # Trigger first to populate data
    client.post("/api/alerts/trigger-check?region_name=Amazon+Wildlife+Reserve")
    
    # Retrieve reports
    response = client.get("/api/reports/")
    assert response.status_code == 200
    reports = response.json()
    assert len(reports) > 0
    assert "recipient_email" in reports[0]
    
    # Download PDF
    report_id = reports[0]["id"]
    response_download = client.get(f"/api/reports/{report_id}/download")
    assert response_download.status_code == 200
    assert response_download.headers["content-type"] == "application/pdf"
