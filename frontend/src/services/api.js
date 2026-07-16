const BASE_URL = '/api';

export const apiService = {
  async getStats() {
    const response = await fetch(`${BASE_URL}/dashboard/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return await response.json();
  },

  async getRecentActivity() {
    const response = await fetch(`${BASE_URL}/dashboard/recent-activity`);
    if (!response.ok) throw new Error('Failed to fetch recent activity');
    return await response.json();
  },

  async getAlerts() {
    const response = await fetch(`${BASE_URL}/alerts/`);
    if (!response.ok) throw new Error('Failed to fetch alerts');
    return await response.json();
  },

  async getAlertDetail(alertId) {
    const response = await fetch(`${BASE_URL}/alerts/${alertId}`);
    if (!response.ok) throw new Error('Failed to fetch alert detail');
    return await response.json();
  },

  async updateAlertStatus(alertId, status, riskLevel = null) {
    const response = await fetch(`${BASE_URL}/alerts/${alertId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, risk_level: riskLevel })
    });
    if (!response.ok) throw new Error('Failed to update alert status');
    return await response.json();
  },

  async getReports() {
    const response = await fetch(`${BASE_URL}/reports/`);
    if (!response.ok) throw new Error('Failed to fetch reports');
    return await response.json();
  },

  async triggerCheck(regionName = "Amazon Wildlife Reserve") {
    const response = await fetch(`${BASE_URL}/alerts/trigger-check?region_name=${encodeURIComponent(regionName)}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to trigger check');
    return await response.json();
  },

  getReportDownloadUrl(reportId) {
    return `${BASE_URL}/reports/${reportId}/download`;
  }
};
