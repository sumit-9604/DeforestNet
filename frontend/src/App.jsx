import React, { useState, useEffect } from 'react';
import { ShieldCheck, LayoutDashboard, Search, Satellite, FileText } from 'lucide-react';
import StatusBar from './components/StatusBar.jsx';
import Dashboard from './components/Dashboard.jsx';
import Investigate from './components/Investigate.jsx';
import Fleet from './components/Fleet.jsx';
import Reports from './components/Reports.jsx';
import { apiService } from './services/api.js';

const TABS = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, Comp: Dashboard },
  { key: 'investigate', label: 'Investigate', icon: Search, Comp: Investigate },
  { key: 'fleet', label: 'Fleet', icon: Satellite, Comp: Fleet },
  { key: 'reports', label: 'Reports', icon: FileText, Comp: Reports },
];

function Brand() {
  return (
    <div className="fg-brand">
      <div className="fg-brand-icon"><ShieldCheck size={18} /></div>
      <div className="fg-brand-text">
        <h1>FOREST<span>GUARD</span></h1>
        <p>Cyber-Surveillance · Agentic AI</p>
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState('dashboard');
  const [alerts, setAlerts] = useState([]);
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [alertsData, reportsData, statsData, activityData] = await Promise.all([
        apiService.getAlerts(),
        apiService.getReports(),
        apiService.getStats(),
        apiService.getRecentActivity()
      ]);
      setAlerts(alertsData);
      setReports(reportsData);
      setStats(statsData);
      setActivity(activityData);
    } catch (err) {
      console.error("Error loading live data from backend:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const Active = TABS.find((t) => t.key === tab).Comp;

  return (
    <div className="fg-app">
      <div className="fg-layout">
        <aside className="fg-sidebar">
          <Brand />
          <nav className="fg-sidebar-nav">
            {TABS.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.key}
                  className={`fg-sidebar-item ${tab === t.key ? 'active' : ''}`}
                  onClick={() => setTab(t.key)}
                >
                  <Icon size={18} />
                  {t.label}
                </button>
              );
            })}
          </nav>
          <div className="fg-sidebar-foot mono" style={{ cursor: 'pointer' }} onClick={loadData}>
            {loading ? 'SYNCING...' : 'SYNC COMPLETE · REFRESH ↻'}
          </div>
        </aside>

        <div className="fg-main">
          <header className="fg-topbar">
            <div className="fg-topbar-brand"><Brand /></div>
            <StatusBar />
          </header>

          <div className="fg-content">
            {loading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', color: 'var(--mint)', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
                <span className="animate-pulse">SYNCHRONIZING WITH SECURE SERVER...</span>
              </div>
            ) : (
              <Active 
                alerts={alerts} 
                reports={reports} 
                stats={stats} 
                activity={activity} 
                onRefresh={loadData} 
              />
            )}
          </div>

          <nav className="fg-nav">
            {TABS.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.key}
                  className={`fg-nav-item ${tab === t.key ? 'active' : ''}`}
                  onClick={() => setTab(t.key)}
                >
                  <Icon size={19} />
                  {t.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}
