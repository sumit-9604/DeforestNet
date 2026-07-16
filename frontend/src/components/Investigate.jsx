import React, { useState } from 'react';
import { X, CheckCircle2, Lock } from 'lucide-react';
import RingProgress from './RingProgress.jsx';

const CASES = [
  { id: 1, sector: 'Sector 4-X', time: '3:30 PM', status: 'detected', confidence: 98 },
  { id: 2, sector: 'Sector 7-G', time: '3:40 PM', status: 'detected', confidence: 91 },
  { id: 3, sector: 'Sector 2-C', time: '5:30 PM', status: 'pending', confidence: 64 },
  { id: 4, sector: 'Sector 9-K', time: '3:30 AM', status: 'detected', confidence: 87 },
  { id: 5, sector: 'Sector 1-A', time: '3:53 AM', status: 'pending', confidence: 55 },
  { id: 6, sector: 'Sector 5-M', time: '3:39 PM', status: 'detected', confidence: 94 },
];

function CaseModal({ item, onClose }) {
  return (
    <div className="fg-modal-backdrop" onClick={onClose}>
      <div className="fg-modal fg-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="fg-modal-head">
          <h2>CASE FILE: {item.sector.toUpperCase()}</h2>
          <button onClick={onClose}><X size={16} /></button>
        </div>

        <div className="fg-slider">
          <div className="before">BEFORE — CANOPY INTACT</div>
          <div className="after">AFTER — CLEARED</div>
          <div className="handle" />
        </div>

        <div className="fg-checklist">
          <div className="item"><CheckCircle2 size={16} /> Protected area confirmed</div>
          <div className="item"><CheckCircle2 size={16} /> No valid permits found</div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', margin: '14px 0 4px' }}>
          <div className="fg-gauge-wrap">
            <RingProgress value={item.confidence} size={100} color="var(--mint)" label="CONFIDENCE" />
            <div className="fg-gauge-label" style={{ color: 'var(--mint)' }}>High confidence: illegal activity</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Investigate() {
  const [selected, setSelected] = useState(null);

  return (
    <div>
      <div className="fg-page-title">Evidence & Investigation Vault</div>
      <div style={{ margin: '0 14px 14px', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
        <Lock size={12} /> Chain-of-custody verified for all case files
      </div>
      <div className="fg-vault-grid">
        {CASES.map((c) => (
          <button key={c.id} className="fg-case-card" onClick={() => setSelected(c)}>
            <div className="fg-case-thumb">
              <div className="hotspot" style={{ top: '35%', left: '45%' }} />
              <div className="hotspot" style={{ top: '55%', left: '65%', width: 10, height: 10 }} />
            </div>
            <div className="fg-case-body">
              <div className="fg-case-time">CASE FILE · {c.time}</div>
              <div className={`fg-case-status ${c.status}`}>
                {c.status === 'detected' ? 'DETECTED DEFORESTATION' : 'PENDING REVIEW'}
              </div>
            </div>
          </button>
        ))}
      </div>
      {selected && <CaseModal item={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
