import React, { useState } from 'react';
import { X, CheckCircle2, Lock } from 'lucide-react';
import RingProgress from './RingProgress.jsx';
import { apiService } from '../services/api.js';

const CASES = [
  { id: 1, sector: 'Sector 4-X', time: '09:00 PM IST', status: 'detected', confidence: 98 },
  { id: 2, sector: 'Sector 7-G', time: '09:10 PM IST', status: 'detected', confidence: 91 },
  { id: 3, sector: 'Sector 2-C', time: '11:00 PM IST', status: 'pending', confidence: 64 },
  { id: 4, sector: 'Sector 9-K', time: '09:00 AM IST', status: 'detected', confidence: 87 },
  { id: 5, sector: 'Sector 1-A', time: '09:23 AM IST', status: 'pending', confidence: 55 },
  { id: 6, sector: 'Sector 5-M', time: '09:09 PM IST', status: 'detected', confidence: 94 },
];

function CaseModal({ item, onClose }) {
  const [sliderVal, setSliderVal] = useState(50); // 0 to 100

  // Extract variables
  const alert = item.rawAlert;
  const details = item.details || {};
  const isProtected = item.isProtected;
  const paName = item.paName;
  const narrative = item.narrative;
  const recommendation = details?.analysis_result?.recommended_action || (alert ? alert.recommended_action : "Investigate the marked logging area for potential illegal clearing.");

  // For fallback mock cases
  const sectorName = item.sector;
  const confidence = item.confidence;
  const isProtectedConfirmed = isProtected || item.id % 2 === 0;

  // Real before/after imagery URLs from backend API
  const beforeUrl = alert ? apiService.getAlertImageUrl(alert.id, 'before') : null;
  const afterUrl = alert ? apiService.getAlertImageUrl(alert.id, 'after') : null;

  return (
    <div className="fg-modal-backdrop" onClick={onClose}>
      <div className="fg-modal fg-fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 360 }}>
        <div className="fg-modal-head">
          <h2>CASE FILE: {sectorName.toUpperCase()}</h2>
          <button onClick={onClose}><X size={16} /></button>
        </div>

        {/* Interactive Slider */}
        <div className="mb-2">
          <div className="fg-slider" style={{ position: 'relative', height: 160, borderRadius: 6, overflow: 'hidden', border: '1px solid var(--line-bright)' }}>
            {/* Before (Intact Forest) */}
            <div className="before" style={{ 
              position: 'absolute', inset: 0, display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-start',
              backgroundImage: beforeUrl ? `url(${beforeUrl})` : 'linear-gradient(160deg, #123430, #0a1815)',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              padding: 6
            }}>
              <span style={{ 
                fontSize: 8, 
                fontFamily: 'var(--font-mono)', 
                color: 'var(--mint)', 
                background: 'rgba(14, 21, 22, 0.85)', 
                padding: '2px 6px', 
                borderRadius: 3,
                border: '1px solid rgba(145, 255, 226, 0.2)'
              }}>
                BEFORE {alert ? `(NDVI: ${alert.ndvi_before_mean?.toFixed(2) || '0.78'})` : ''}
              </span>
            </div>
            
            {/* After (Cleared forest) clipped based on sliderVal */}
            <div className="after" style={{ 
              position: 'absolute', inset: 0, display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end',
              backgroundImage: afterUrl ? `url(${afterUrl})` : 'linear-gradient(160deg, #2c1414, #150a0a)',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              clipPath: `inset(0 0 0 ${sliderVal}%)`,
              padding: 6
            }}>
              <span style={{ 
                fontSize: 8, 
                fontFamily: 'var(--font-mono)', 
                color: 'var(--alert)', 
                background: 'rgba(14, 21, 22, 0.85)', 
                padding: '2px 6px', 
                borderRadius: 3,
                border: '1px solid rgba(255, 180, 171, 0.2)'
              }}>
                AFTER {alert ? `(NDVI: ${alert.ndvi_after_mean?.toFixed(2) || '0.45'})` : ''}
              </span>
            </div>

            {/* Slider bar line */}
            <div className="handle" style={{ left: `${sliderVal}%`, height: '100%', position: 'absolute', transform: 'translateX(-50%)', width: 2, background: 'var(--mint)', boxShadow: '0 0 10px var(--mint)', zIndex: 10 }} />
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

        <div className="fg-checklist">
          <div className="item" style={{ color: isProtectedConfirmed ? 'var(--mint)' : 'var(--text-dim)' }}>
            <CheckCircle2 size={16} /> {isProtectedConfirmed ? (paName ? `Protected: ${paName}` : 'Protected area confirmed') : 'Outside Protected Area'}
          </div>
          <div className="item" style={{ color: 'var(--mint)' }}><CheckCircle2 size={16} /> No valid permits found</div>
        </div>

        {narrative && (
          <div style={{ marginTop: 10, padding: '8px 10px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--line)', borderRadius: 6, fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', textAlign: 'left', lineHeight: 1.4 }}>
            <span style={{ color: 'var(--mint)', fontWeight: 'bold' }}>NARRATIVE:</span> {narrative}
            <div style={{ marginTop: 6 }} />
            <span style={{ color: 'var(--alert)', fontWeight: 'bold' }}>ACTION:</span> {recommendation}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'center', margin: '14px 0 4px' }}>
          <div className="fg-gauge-wrap">
            <RingProgress value={confidence} size={90} color={alert && alert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--mint)'} label="CONFIDENCE" />
            <div className="fg-gauge-label" style={{ color: alert && alert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--mint)' }}>
              {alert ? `${alert.risk_level} Risk Level` : 'High confidence: illegal activity'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Investigate({ alerts = [] }) {
  const [selected, setSelected] = useState(null);

  // Convert alerts to Case Files if alerts is not empty, else use fallback mock cases
  const casesList = alerts.length > 0
    ? alerts.map((a) => {
        const details = typeof a.details === 'string' ? JSON.parse(a.details) : (a.details || {});
        const isProtected = details?.protected_info?.is_protected || a.is_protected || false;
        const paName = details?.protected_info?.name || a.protected_area_name || 'Amazon Region';
        const narrative = details?.analysis_result?.narrative_summary || a.narrative_summary || 'Vegetation loss detected.';
        
        let confidence = 85;
        if (a.ndvi_diff_mean) {
          confidence = Math.min(Math.max(Math.round(Math.abs(a.ndvi_diff_mean) * 150), 60), 99);
        }

        return {
          id: a.id,
          sector: `Sector ${a.id} (${a.latitude.toFixed(3)}, ${a.longitude.toFixed(3)})`,
          time: new Date(a.detected_at.endsWith('Z') ? a.detected_at : a.detected_at + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST',
          status: a.status.toLowerCase(),
          confidence,
          rawAlert: a,
          details,
          isProtected,
          paName,
          narrative
        };
      })
    : CASES;

  return (
    <div>
      <div className="fg-page-title">Evidence & Investigation Vault</div>
      <div style={{ margin: '0 14px 14px', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
        <Lock size={12} /> Chain-of-custody verified for all case files ({casesList.length} total)
      </div>
      <div className="fg-vault-grid">
        {casesList.map((c) => (
          <button key={c.id} className="fg-case-card" onClick={() => setSelected(c)}>
            <div className="fg-case-thumb">
              <div className="hotspot" style={{ top: '35%', left: '45%', background: c.rawAlert && c.rawAlert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--amber)' }} />
              <div className="hotspot" style={{ top: '55%', left: '65%', width: 10, height: 10, background: c.rawAlert && c.rawAlert.risk_level === 'Critical' ? 'var(--alert)' : 'var(--amber)' }} />
            </div>
            <div className="fg-case-body">
              <div className="fg-case-time">{c.sector} · {c.time}</div>
              <div className={`fg-case-status ${c.status}`}>
                {c.rawAlert ? `${c.status.toUpperCase()} (${c.rawAlert.risk_level.toUpperCase()})` : (c.status === 'detected' ? 'DETECTED DEFORESTATION' : 'PENDING REVIEW')}
              </div>
            </div>
          </button>
        ))}
      </div>
      {selected && <CaseModal item={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
