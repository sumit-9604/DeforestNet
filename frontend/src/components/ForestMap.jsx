import React, { useEffect, useMemo } from 'react';
import { Brain } from 'lucide-react';
import {
  CircleMarker,
  LayersControl,
  MapContainer,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const AMAZON_CENTER = [-3.46, -62.21];

const RISK_COLORS = {
  Critical: '#ff5559',
  High: '#ffb4ab',
  Medium: '#ffcf70',
  Low: '#91ffe2',
};

function AlertBounds({ alerts }) {
  const map = useMap();

  useEffect(() => {
    if (!alerts.length) {
      map.setView(AMAZON_CENTER, 10);
      return;
    }

    const points = alerts
      .filter((alert) => Number.isFinite(alert.latitude) && Number.isFinite(alert.longitude))
      .map((alert) => [alert.latitude, alert.longitude]);

    if (points.length === 1) {
      map.flyTo(points[0], 12, { duration: 0.8 });
    } else if (points.length > 1) {
      map.fitBounds(points, { padding: [42, 42], maxZoom: 12 });
    }
  }, [alerts, map]);

  return null;
}

function getAgentState(alerts) {
  if (!alerts.length) return { label: 'STANDBY', color: 'var(--text-dim)' };
  if (alerts.some((alert) => alert.risk_level === 'Critical')) return { label: 'CRITICAL', color: 'var(--alert)' };
  if (alerts.some((alert) => alert.risk_level === 'High')) return { label: 'HIGH ALERT', color: 'var(--amber)' };
  if (alerts.some((alert) => alert.status === 'Pending')) return { label: 'REASONING', color: 'var(--mint)' };
  return { label: 'NOMINAL', color: 'var(--mint)' };
}

export default function ForestMap({ alerts = [] }) {
  const validAlerts = useMemo(
    () => alerts.filter((alert) => Number.isFinite(alert.latitude) && Number.isFinite(alert.longitude)),
    [alerts],
  );
  const agentState = getAgentState(validAlerts);

  return (
    <div className="fg-panel dfn-map-panel fg-fade-in" style={{ padding: 12 }}>
      <div className="fg-taskid">
        <span>LIVE FOREST MONITORING MAP <b>· SATELLITE + STREET</b></span>
        <span style={{ color: validAlerts.some((alert) => ['Critical', 'High'].includes(alert.risk_level)) ? 'var(--alert)' : 'var(--mint)' }}>
          ● {validAlerts.length} ACTIVE
        </span>
      </div>

      <div className="dfn-map-frame live-forest-map">
        <MapContainer center={AMAZON_CENTER} zoom={10} scrollWheelZoom className="leaflet-map">
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="Satellite imagery">
              <TileLayer
                attribution="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community"
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              />
            </LayersControl.BaseLayer>
            <LayersControl.BaseLayer name="Street map">
              <TileLayer
                attribution="© OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>
          </LayersControl>

          <AlertBounds alerts={validAlerts} />

          {validAlerts.map((alert) => {
            const color = RISK_COLORS[alert.risk_level] || '#4cd6fb';
            return (
              <CircleMarker
                key={alert.id}
                center={[alert.latitude, alert.longitude]}
                radius={alert.risk_level === 'Critical' ? 12 : 9}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.78, weight: 2 }}
              >
                <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
                  Sector {alert.id} · {alert.risk_level || 'Unclassified'}
                </Tooltip>
                <Popup>
                  <div className="dfn-map-popup">
                    <strong>{alert.risk_level || 'Pending'} deforestation alert</strong>
                    <span>Sector {alert.id}</span>
                    <span>Area: {Number(alert.area_ha || 0).toFixed(2)} ha</span>
                    <span>Status: {alert.status}</span>
                    <span>Coordinates: {alert.latitude.toFixed(5)}, {alert.longitude.toFixed(5)}</span>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>

        <div className="dfn-overlay-stats live-map-status">
          <div className="hud-glass live-map-status-card">
            <div className="live-map-status-title">Agent state</div>
            <div className="live-map-status-value" style={{ color: agentState.color }}>
              <Brain size={14} /> {agentState.label}
            </div>
            <div className="live-map-status-caption">Auto-sync every 30 seconds</div>
          </div>
        </div>
      </div>
    </div>
  );
}
