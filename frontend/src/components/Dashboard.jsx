import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, AlertTriangle, Satellite, Database, Flame } from 'lucide-react';
import RingProgress from './RingProgress.jsx';
import LiveConsole from './LiveConsole.jsx';
import ForestMap from './ForestMap.jsx';

const TASKS = [
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
        <RingProgress value={task.value} label={task.value < 20 ? 'INIT' : (task.value === 100 ? 'DONE' : 'ACTIVE')} />
        <div>
          <div className="fg-task-name">{task.name}</div>
          <div className="fg-task-status" style={{ color: task.value === 100 ? 'var(--mint)' : 'var(--text)' }}>
            ● {task.status}
          </div>
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
  const [tasks, setTasks] = useState(TASKS);
  const prevAlertsLength = useRef(alerts.length);
  const activeAlert = alerts.find(a => a.risk_level === 'Critical' || a.risk_level === 'High') || alerts[0];

  // 1. Reset tasks when a new check is triggered (detected by alert count increasing)
  useEffect(() => {
    if (alerts.length > prevAlertsLength.current) {
      setTasks([
        { ...TASKS[0], value: 12, status: 'IN PROGRESS' },
        { ...TASKS[1], value: 5, status: 'IN PROGRESS' },
        { ...TASKS[2], value: 0, status: 'INITIATING' }
      ]);
    }
    prevAlertsLength.current = alerts.length;
  }, [alerts]);

  // 2. Increment progress over time to simulate active pipeline processing
  useEffect(() => {
    const interval = setInterval(() => {
      setTasks(prevTasks => 
        prevTasks.map(t => {
          if (t.value < 100) {
            const increment = Math.floor(Math.random() * 8) + 2; // increase by 2% to 10%
            const nextVal = Math.min(t.value + increment, 100);
            return {
              ...t,
              value: nextVal,
              status: nextVal === 100 ? 'COMPLETED' : 'IN PROGRESS'
            };
          }
          return t;
        })
      );
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <ForestMap alerts={alerts} stats={stats} />

      {/* Grid of Aggregated Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, margin: '20px 14px 20px' }}>
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

      {activeAlert ? (
        <div 
          className="fg-alert-banner fg-fade-in" 
          style={{ 
            background: 'rgba(147, 0, 10, 0.15)',
            border: '2px solid var(--alert)',
            padding: '12px 16px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            boxShadow: '0 0 15px rgba(255, 180, 171, 0.1)',
            marginTop: stats ? 0 : 20,
            marginLeft: 14,
            marginRight: 14,
            width: 'calc(100% - 28px)'
          }}
        >
          <div className="pulse-ring" style={{ animationDuration: '3s', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--alert)' }}>
            <AlertTriangle size={24} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '15px', color: 'var(--alert)', fontWeight: '600', letterSpacing: '-0.02em', textTransform: 'uppercase' }}>
              {activeAlert.risk_level} ALERT: {activeAlert.status.toUpperCase()}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'rgba(255, 180, 171, 0.8)', letterSpacing: '0.5px' }}>
              SECTOR {activeAlert.id} | COORD {activeAlert.latitude?.toFixed(4)}, {activeAlert.longitude?.toFixed(4)}
            </span>
          </div>
        </div>
      ) : (
        <div 
          className="fg-alert-banner fg-fade-in" 
          style={{ 
            background: 'rgba(147, 0, 10, 0.15)',
            border: '2px solid var(--alert)',
            padding: '12px 16px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            boxShadow: '0 0 15px rgba(255, 180, 171, 0.1)',
            marginTop: 20,
            marginLeft: 14,
            marginRight: 14,
            width: 'calc(100% - 28px)'
          }}
        >
          <div className="pulse-ring" style={{ animationDuration: '3s', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--alert)' }}>
            <AlertTriangle size={24} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '15px', color: 'var(--alert)', fontWeight: '600', letterSpacing: '-0.02em', textTransform: 'uppercase' }}>
              ILLEGAL LOGGING DETECTED
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'rgba(255, 180, 171, 0.8)', letterSpacing: '0.5px' }}>
              SECTOR 7-G | COORD 45.2, -122.3
            </span>
          </div>
        </div>
      )}

      <div className="fg-page-title">Task Execution Log</div>
      <div className="fg-grid">
        {tasks.map((t) => <TaskCard key={t.id} task={t} />)}
      </div>

      <LiveConsole lines={activity.map(a => {
        const utcStr = a.timestamp.endsWith('Z') ? a.timestamp : a.timestamp + 'Z';
        const time = new Date(utcStr).toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          timeZone: 'Asia/Kolkata'
        });
        return `${time} - ${a.message}`;
      })} />
    </div>
  );
}
