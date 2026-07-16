import React from 'react';
import { Satellite, RadioTower, Plane } from 'lucide-react';

const NODES = [
  { name: 'Sentinel-2 Constellation', icon: Satellite, status: 'OPTIMAL', pct: 96, detail: 'latency 1.2s' },
  { name: 'Regional GLAD Sensors', icon: RadioTower, status: 'ACTIVE', pct: 88, detail: 'coverage 88%' },
  { name: 'Autonomous Drone Squadron Alpha', icon: Plane, status: 'IN FLIGHT', pct: 75, detail: 'batt 75%' },
];

const METRICS = [
  { label: 'Latency', value: '34ms', sub: 'avg' },
  { label: 'AI Load', value: '68%', sub: 'processing' },
  { label: 'Memory', value: '82%', sub: 'available' },
];

function Radar() {
  return (
    <svg width={200} height={200} viewBox="0 0 200 200">
      {[90, 68, 46, 24].map((r) => (
        <circle key={r} cx="100" cy="100" r={r} fill="none" stroke="var(--line)" strokeWidth="1" />
      ))}
      <line x1="10" y1="100" x2="190" y2="100" stroke="var(--line)" strokeWidth="1" />
      <line x1="100" y1="10" x2="100" y2="190" stroke="var(--line)" strokeWidth="1" />
      <defs>
        <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--mint)" stopOpacity="0.5" />
          <stop offset="100%" stopColor="var(--mint)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M100,100 L100,10 A90,90 0 0,1 163,37 Z" fill="url(#sweep)">
        <animateTransform attributeName="transform" type="rotate" from="0 100 100" to="360 100 100" dur="4s" repeatCount="indefinite" />
      </path>
      <circle cx="140" cy="70" r="3" fill="var(--mint)" />
      <circle cx="70" cy="130" r="3" fill="var(--blue)" />
      <circle cx="100" cy="100" r="3" fill="var(--text)" />
    </svg>
  );
}

export default function Fleet() {
  return (
    <div>
      <div className="fg-page-title">Autonomous Fleet & Sensor Status</div>

      <div className="fg-radar-wrap"><Radar /></div>
      <div style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-dim)', marginBottom: 10 }}>
        SCANNING… COVERAGE AREA 94%
      </div>

      <div className="fg-metric-row">
        <span>DATA NODES ONLINE: <b>12/15</b></span>
      </div>

      <div className="fg-grid">
        {NODES.map((n) => {
          const Icon = n.icon;
          return (
            <div className="fg-fleet-item" key={n.name}>
              <div className="head">
                <Icon size={16} className="icon" />
                <span className="name">{n.name}</span>
                <span className="stat">{n.status}</span>
              </div>
              <div className="fg-bar-track"><div className="fg-bar-fill" style={{ width: `${n.pct}%` }} /></div>
            </div>
          );
        })}
      </div>

      <div className="fg-page-title" style={{ marginTop: 20 }}>System Health</div>
      <div className="fg-spark-row">
        {METRICS.map((m) => (
          <div className="fg-spark-card" key={m.label}>
            <div className="val">{m.value}</div>
            <div className="lbl">{m.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
