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
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to update alert status');
    }
    return await response.json();
  },

  async getReports() {
    const response = await fetch(`${BASE_URL}/reports/`);
    if (!response.ok) throw new Error('Failed to fetch reports');
    return await response.json();
  },

  async triggerCheck(regionName = "Amazon Wildlife Reserve", humanOversight = true) {
    const response = await fetch(`${BASE_URL}/alerts/trigger-check?region_name=${encodeURIComponent(regionName)}&human_oversight=${humanOversight}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to trigger check');
    return await response.json();
  },

  getReportDownloadUrl(reportId) {
    return `${BASE_URL}/reports/${reportId}/download`;
  },

  getAlertImageUrl(alertId, timeframe) {
    return `${BASE_URL}/alerts/${alertId}/image/${timeframe}`;
  },

  getAlertComparisonUrl(alertId) {
    return `${BASE_URL}/alerts/${alertId}/comparison`;
  },

  async getSettings() {
    const response = await fetch(`${BASE_URL}/settings/`);
    if (!response.ok) throw new Error('Failed to fetch settings');
    return await response.json();
  },

  async updateSettings(simulationMode) {
    const response = await fetch(`${BASE_URL}/settings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ simulation_mode: simulationMode })
    });
    if (!response.ok) throw new Error('Failed to update settings');
    return await response.json();
  }
};
