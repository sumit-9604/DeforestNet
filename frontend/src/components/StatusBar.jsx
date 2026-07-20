import React, { useEffect, useState } from 'react';
import { Radio } from 'lucide-react';
import { apiService } from '../services/api.js';

export default function StatusBar() {
  const [time, setTime] = useState(new Date());
  const [simulationMode, setSimulationMode] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Fetch initial settings
  useEffect(() => {
    async function fetchSettings() {
      try {
        const settings = await apiService.getSettings();
        setSimulationMode(settings.simulation_mode);
      } catch (err) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchSettings();
  }, []);

  const handleToggle = async () => {
    const nextMode = !simulationMode;
    // optimistic update
    setSimulationMode(nextMode);
    try {
      await apiService.updateSettings(nextMode);
    } catch (err) {
      console.error("Failed to update settings:", err);
      // rollback
      setSimulationMode(simulationMode);
    }
  };

  const ist = time.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Kolkata'
  });

  return (
    <div className="fg-statusbar" style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
      <button
        onClick={handleToggle}
        disabled={loading}
        className="mono"
        style={{
          background: simulationMode ? 'rgba(255, 179, 176, 0.1)' : 'rgba(145, 255, 226, 0.1)',
          border: `1px solid ${simulationMode ? 'var(--amber)' : 'var(--mint)'}`,
          color: simulationMode ? 'var(--amber)' : 'var(--mint)',
          borderRadius: 4,
          padding: '4px 8px',
          fontSize: 10,
          fontWeight: 'bold',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 6
        }}
      >
        <span className="dot" style={{ 
          background: simulationMode ? 'var(--amber)' : 'var(--mint)', 
          boxShadow: `0 0 6px ${simulationMode ? 'var(--amber)' : 'var(--mint)'}`,
          margin: 0
        }} />
        {simulationMode ? 'SIMULATION MODE' : 'LIVE PRODUCTION'}
      </button>

      <span className="ticker-item"><span className="dot" /> System nominal</span>
      <span className="ticker-item mono">{ist} IST</span>
      <span className="ticker-item"><Radio size={12} /> Uplink stable</span>
    </div>
  );
}
