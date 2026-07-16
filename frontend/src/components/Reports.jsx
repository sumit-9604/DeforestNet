import React, { useState } from 'react';
import { TreePine, Volume2, Plane, ThermometerSun, ShieldAlert, MessageSquareWarning, FileCheck2, CheckCircle2, Fingerprint } from 'lucide-react';

export default function Reports() {
  const [sent, setSent] = useState(false);

  return (
    <div>
      <div className="fg-page-title">Automated Reporting & Authority Portal</div>

      <div className="fg-grid-2">
        <div className="fg-report-doc">
          <h3>INCIDENT-8092B</h3>
          <div className="meta"><span>SECTOR 7 · GREENZONE ALPHA</span><span>AI AGENT: SENTINEL-X</span></div>

          <div className="fg-page-title" style={{ margin: '0 0 8px', fontSize: 11 }}>Incident Summary</div>
          <ul className="fg-report-list">
            <li><TreePine size={14} /> Detection of unauthorized logging activity</li>
            <li><Volume2 size={14} /> Multiple chainsaw acoustic signatures confirmed</li>
            <li><Plane size={14} /> Drone surveillance imagery acquired</li>
            <li><ThermometerSun size={14} /> Estimated area affected: 2.5 hectares</li>
          </ul>

          <div className="fg-page-title" style={{ margin: '16px 0 8px', fontSize: 11 }}>Recommended Enforcement</div>
          <ul className="fg-report-list">
            <li><Plane size={14} /> Deploy autonomous response drones for containment</li>
            <li><ShieldAlert size={14} /> Alert local enforcement units for interception</li>
            <li><MessageSquareWarning size={14} /> Issue cease &amp; desist warning via area broadcast</li>
            <li><FileCheck2 size={14} /> Prepare digital evidence package for prosecution</li>
          </ul>
        </div>

        <div>
          <div className="fg-oversight-row">
            <span>Human oversight</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--mint)' }}>
              ACTIVE <span className="fg-toggle-pill" />
            </span>
          </div>

          <div className="fg-page-title" style={{ fontSize: 11 }}>Recipients</div>
          <div className="fg-recipient-row">
            <span className="name">Ministry of Environment</span>
            <CheckCircle2 size={16} className="check" />
          </div>
          <div className="fg-recipient-row">
            <span className="name">Local Enforcement Units</span>
            <CheckCircle2 size={16} className="check" />
          </div>

          <button className="fg-authorize-btn" onClick={() => setSent(true)} disabled={sent}>
            <Fingerprint size={18} />
            <span>
              {sent ? 'NOTIFICATION SENT' : 'AUTHORIZE NOTIFICATION'}
              <small>Send evidence package · initiate enforcement protocols</small>
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
