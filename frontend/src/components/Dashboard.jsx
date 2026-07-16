import React, { useState, useEffect } from 'react';
import { ChevronDown, AlertTriangle, Satellite, Database, Flame } from 'lucide-react';
import RingProgress from './RingProgress.jsx';
import LiveConsole from './LiveConsole.jsx';

const BASE_TASKS = [
  {
    id: '0x4F7B2A1E',
    name: 'Analyzing Sentinel-2 spectral data',
    value: 68,
    status: 'IN PROGRESS',
    icon: Satellite,
    trace: [
      ['TRIGGER', 'Spectral anomaly detected in NIR band, sector 7G'],
      ['ACTION', 'Fetching LIC imagery from orbital node 3'],
      ['PROCESSING', 'Multi-temporal NDVI calc for vegetation stress'],
      ['PREDICTION', '88% probability of illegal logging activity'],
      ['NEXT', 'Correlating with ground sensor array'],
    ],
  },
  {
    id: '0x9C1E4D8B',
    name: 'Cross-referencing land ownership records',
    value: 45,
    status: 'IN PROGRESS',
    icon: Database,
    trace: [
      ['CONTEXT', 'Investigating ownership change, parcel #9120-A'],
      ['SOURCE', 'Querying regional land registry (GD-9)'],
      ['CONSTRAINT', 'Access restricted — initiating secure 2FA'],
      ['RISK', 'Potential fraudulent title transfer flagged'],
      ['CURRENT', 'Parsing deed document metadata'],
    ],
  },
  {
    id: '0xB2F5A3C7',
    name: 'Generating probabilistic fire risk assessment',
    value: 12,
    status: 'INITIATING',
    icon: Flame,
    trace: [
      ['GOAL', 'Evaluate forest fire risk for upcoming season'],
      ['MODEL', 'Integrating climate, fuel moisture, historical fire data'],
      ['STATUS', 'Calibrating Bayesian network'],
    ],
  },
];

function TaskCard({ task }) {
  const [open, setOpen] = useState(false);
  const Icon = task.icon;
  return (
    <div className="fg-panel fg-fade-in">
      <div className="fg-taskid">
        <span>TASK <b>{task.id}</b></span>
        <Icon size={14} color="var(--text-dim)" />
      </div>
      <div className="fg-ring-row">
        <RingProgress value={task.value} label={task.value < 20 ? 'INIT' : 'ACTIVE'} />
        <div>
          <div className="fg-task-name">{task.name}</div>
          <div className="fg-task-status">● {task.status}</div>
        </div>
      </div>
      <button className={`fg-reasoning-toggle ${open ? 'open' : ''}`} onClick={() => setOpen(!open)}>
        REASONING <ChevronDown size={14} />
      </button>
      {open && (
        <div className="fg-reasoning-body fg-fade-in">
          {task.trace.map(([tag, txt], i) => (
            <div key={i}><span className="tag">→ {tag}:</span><span className="hi"> {txt}</span></div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Dashboard({ alerts = [], stats = null, activity = [] }) {
  // Try to find the latest critical/high alert to show in the header banner
  const activeAlert = alerts.find(a => a.risk_level === 'Critical' || a.risk_level === 'High') || alerts[0];

  return (
    <div>
      {activeAlert && (
        <div className="fg-alert-banner fg-fade-in" style={{ borderColor: activeAlert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--amber)' }}>
          <div className="icon" style={{ color: activeAlert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--amber)' }}>
            <AlertTriangle size={18} />
          </div>
          <div className="txt">
            <div className="eyebrow" style={{ color: activeAlert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--amber)' }}>
              {activeAlert.risk_level} Alert
            </div>
            <div className="title">
              {activeAlert.status} anomaly · Lat {activeAlert.latitude.toFixed(4)}, Lon {activeAlert.longitude.toFixed(4)}
            </div>
          </div>
        </div>
      )}

      {/* Grid of Aggregated Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, margin: '0 14px 20px' }}>
          <div className="fg-panel" style={{ padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--text-dim)', fontFamily: 'var(--font-ui)' }}>Total Alerts</div>
            <div style={{ fontSize: 20, fontWeight: 'bold', fontFamily: 'var(--font-mono)', color: 'var(--mint)', marginTop: 4 }}>{stats.metrics.total_alerts}</div>
          </div>
          <div className="fg-panel" style={{ padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--text-dim)', fontFamily: 'var(--font-ui)' }}>Area Affected</div>
            <div style={{ fontSize: 20, fontWeight: 'bold', fontFamily: 'var(--font-mono)', color: 'var(--mint)', marginTop: 4 }}>{stats.metrics.verified_area_lost_ha} <span style={{ fontSize: 10 }}>ha</span></div>
          </div>
          <div className="fg-panel" style={{ padding: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--text-dim)', fontFamily: 'var(--font-ui)' }}>Resolved Reports</div>
            <div style={{ fontSize: 20, fontWeight: 'bold', fontFamily: 'var(--font-mono)', color: 'var(--mint)', marginTop: 4 }}>{stats.metrics.resolved_reports}</div>
          </div>
        </div>
      )}

      <div className="fg-page-title">Task Execution Log</div>
      <div className="fg-grid">
        {BASE_TASKS.map((t) => <TaskCard key={t.id} task={t} />)}
      </div>

      <LiveConsole lines={activity.map(a => `${a.timestamp.slice(11, 19)} - ${a.message}`)} />
    </div>
  );
}
