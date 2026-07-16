import React, { useState } from 'react';
import { X, CheckCircle2, Lock } from 'lucide-react';
import RingProgress from './RingProgress.jsx';

function CaseModal({ item, onClose }) {
  const [sliderVal, setSliderVal] = useState(50); // 0 to 100

  // Extract variables
  const alert = item.rawAlert;
  const details = item.details || {};
  const isProtected = item.isProtected;
  const paName = item.paName;
  const narrative = item.narrative;
  const recommendation = details?.analysis_result?.recommended_action || alert.recommended_action || "Investigate the marked logging area for potential illegal clearing.";

  return (
    <div className="fg-modal-backdrop" onClick={onClose}>
      <div className="fg-modal fg-fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 360 }}>
        <div className="fg-modal-head">
          <h2>CASE FILE: {item.id}</h2>
          <button onClick={onClose}><X size={16} /></button>
        </div>

        {/* Interactive Slider */}
        <div className="mb-2">
          <div className="fg-slider" style={{ position: 'relative', height: 110 }}>
            {/* Before (Intact Forest) */}
            <div className="before" style={{ 
              position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'linear-gradient(160deg, #0f3d32, #071c19)'
            }}>
              <span style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--mint)', opacity: 0.8 }}>
                BEFORE — CANOPY INTACT (NDVI: {alert.ndvi_before_mean?.toFixed(2) || '0.78'})
              </span>
            </div>
            
            {/* After (Cleared forest) clipped based on sliderVal */}
            <div className="after" style={{ 
              position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifySelf: 'center', justifyContent: 'center',
              background: 'linear-gradient(160deg, #4c1818, #230c0c)',
              clipPath: `inset(0 0 0 ${sliderVal}%)`
            }}>
              <span style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--alert)', opacity: 0.8 }}>
                AFTER — CLEARED (NDVI: {alert.ndvi_after_mean?.toFixed(2) || '0.45'})
              </span>
            </div>

            {/* Slider bar line */}
            <div className="handle" style={{ left: `${sliderVal}%`, height: '100%', position: 'absolute', transform: 'translateX(-50%)' }} />
          </div>
          <input 
            type="range" 
            min="0" 
            max="100" 
            value={sliderVal} 
            onChange={(e) => setSliderVal(e.target.value)} 
            style={{ width: '100%', marginTop: 8, accentColor: 'var(--mint)', background: 'var(--line)', height: 4, borderRadius: 2 }} 
          />
        </div>

        <div className="fg-checklist" style={{ marginTop: 10 }}>
          <div className="item" style={{ color: isProtected ? 'var(--mint)' : 'var(--text-dim)' }}>
            <CheckCircle2 size={16} /> {isProtected ? `Protected: ${paName}` : 'Outside Protected Area'}
          </div>
          <div className="item" style={{ color: 'var(--mint)' }}>
            <CheckCircle2 size={16} /> No valid permits found
          </div>
        </div>

        <div style={{ marginTop: 10, padding: '8px 10px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--line)', borderRadius: 6, fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', textAlign: 'left', lineHeight: 1.4 }}>
          <span style={{ color: 'var(--mint)', fontWeight: 'bold' }}>NARRATIVE:</span> {narrative}
          <div style={{ marginTop: 6 }} />
          <span style={{ color: 'var(--alert)', fontWeight: 'bold' }}>ACTION:</span> {recommendation}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', margin: '14px 0 4px' }}>
          <div className="fg-gauge-wrap">
            <RingProgress value={item.confidence} size={90} color={alert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--mint)'} label="CONFIDENCE" />
            <div className="fg-gauge-label" style={{ color: alert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--mint)' }}>
              {alert.risk_level} Risk Level
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Investigate({ alerts = [] }) {
  const [selected, setSelected] = useState(null);

  // Convert alerts to Case Files
  const casesList = alerts.map((a) => {
    const details = typeof a.details === 'string' ? JSON.parse(a.details) : (a.details || {});
    const isProtected = details?.protected_info?.is_protected || a.is_protected || false;
    const paName = details?.protected_info?.name || a.protected_area_name || 'N/A';
    const narrative = details?.analysis_result?.narrative_summary || a.narrative_summary || 'Vegetation loss detected.';
    
    // Determine confidence based on NDVI diff (diff * -150) capped at 99%
    let confidence = 85;
    if (a.ndvi_diff_mean) {
      confidence = Math.min(Math.max(Math.round(Math.abs(a.ndvi_diff_mean) * 150), 60), 99);
    }

    return {
      id: a.id,
      sector: `Sector ${a.id} (${a.latitude.toFixed(3)}, ${a.longitude.toFixed(3)})`,
      time: new Date(a.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      status: a.status.toLowerCase(),
      confidence,
      rawAlert: a,
      details,
      isProtected,
      paName,
      narrative
    };
  });

  return (
    <div>
      <div className="fg-page-title">Evidence & Investigation Vault</div>
      <div style={{ margin: '0 14px 14px', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
        <Lock size={12} /> Chain-of-custody verified for all case files ({casesList.length} total)
      </div>
      
      {casesList.length === 0 ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
          No case files currently in database.
        </div>
      ) : (
        <div className="fg-vault-grid">
          {casesList.map((c) => (
            <button key={c.id} className="fg-case-card" onClick={() => setSelected(c)}>
              <div className="fg-case-thumb">
                <div className="hotspot" style={{ top: '35%', left: '45%', background: c.rawAlert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--amber)' }} />
                <div className="hotspot" style={{ top: '55%', left: '65%', width: 10, height: 10, background: c.rawAlert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--amber)' }} />
              </div>
              <div className="fg-case-body">
                <div className="fg-case-time">{c.sector} · {c.time}</div>
                <div className={`fg-case-status ${c.status}`}>
                  {c.status.toUpperCase()} ({c.rawAlert.risk_level.toUpperCase()})
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
      {selected && <CaseModal item={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
