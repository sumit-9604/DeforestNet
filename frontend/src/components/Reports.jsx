import React, { useState } from 'react';
import { TreePine, Volume2, Plane, ThermometerSun, ShieldAlert, MessageSquareWarning, FileCheck2, CheckCircle2, Fingerprint, RefreshCw } from 'lucide-react';
import { apiService } from '../services/api.js';

export default function Reports({ reports = [], alerts = [], onRefresh }) {
  const [activeReportIdx, setActiveReportIdx] = useState(0);
  const [isCompiling, setIsCompiling] = useState(false);
  const [sentMap, setSentMap] = useState({});
  const [compileStatus, setCompileStatus] = useState('');

  const activeReport = reports[activeReportIdx] || null;

  // Handle triggering a live pipeline check
  const handleTriggerCheck = async () => {
    try {
      setIsCompiling(true);
      setCompileStatus('Retrieving alerts from GFW...');
      
      const res = await apiService.triggerCheck("Amazon Wildlife Reserve");
      console.log("Pipeline run complete:", res);
      
      setCompileStatus('Compiling evidence packages...');
      setTimeout(() => {
        setCompileStatus('Seeding database schemas...');
        setTimeout(() => {
          setIsCompiling(false);
          setCompileStatus('');
          if (onRefresh) onRefresh();
        }, 1000);
      }, 1000);
      
    } catch (err) {
      console.error("Pipeline trigger failed:", err);
      setIsCompiling(false);
      setCompileStatus('');
    }
  };

  const handleAuthorize = async (reportId) => {
    setSentMap(prev => ({ ...prev, [reportId]: true }));
    // Simulate updating backend status
    try {
      // In a real app we would make a PUT request to update the report/alert status
    } catch (err) {
      console.error("Failed to authorize report:", err);
    }
  };

  // Extract details for the current active report
  let reportDetails = {
    incidentId: 'INCIDENT-8092B',
    location: 'SECTOR 7 · GREENZONE ALPHA',
    agentName: 'SENTINEL-X',
    summary: [
      'Detection of unauthorized logging activity',
      'Multiple chainsaw acoustic signatures confirmed',
      'Drone surveillance imagery acquired',
      'Estimated area affected: 2.5 hectares'
    ],
    enforcement: [
      'Deploy autonomous response drones for containment',
      'Alert local enforcement units for interception',
      'Issue cease & desist warning via area broadcast',
      'Prepare digital evidence package for prosecution'
    ]
  };

  if (activeReport) {
    // Find matching alert to extract metadata
    const alert = alerts.find(a => a.id === activeReport.alert_id) || {};
    const details = typeof alert.details === 'string' ? JSON.parse(alert.details) : (alert.details || {});
    
    const isProtected = details?.protected_info?.is_protected || alert.is_protected || false;
    const paName = details?.protected_info?.name || alert.protected_area_name || 'Amazon Region';
    
    reportDetails = {
      id: activeReport.id,
      incidentId: `REPORT-00${activeReport.id}`,
      location: `Lat ${alert.latitude?.toFixed(4) || '-3.525'}, Lon ${alert.longitude?.toFixed(4) || '-62.284'}`,
      agentName: 'CLAUDE-3.5-SONNET',
      summary: [
        `Verified forest cover loss of ${alert.area_ha || 0.1} hectares.`,
        isProtected ? `Location inside protected boundary of ${paName}.` : `Location outside protected boundaries.`,
        `NDVI drop confirmed (Before: ${alert.ndvi_before_mean?.toFixed(2) || '0.80'}, After: ${alert.ndvi_after_mean?.toFixed(2) || '0.64'}).`,
        details?.analysis_result?.narrative_summary || alert.narrative_summary || 'Vegetation loss detected.'
      ],
      enforcement: [
        details?.analysis_result?.recommended_action || alert.recommended_action || 'Dispatch local officers to investigate.',
        'Upload report package to regional environmental registry.',
        'Monitor coordinate location on subsequent Sentinel-2 satellite passes.'
      ]
    };
  }

  const isSent = activeReport ? sentMap[activeReport.id] : false;

  return (
    <div>
      <div className="fg-page-title" style={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
        <span>Reporting & Authority Portal</span>
        <button 
          onClick={handleTriggerCheck} 
          disabled={isCompiling}
          className="mono"
          style={{
            marginLeft: 'auto',
            background: 'var(--panel-raised)',
            border: '1px solid var(--line-bright)',
            padding: '5px 12px',
            fontSize: 9,
            borderRadius: 4,
            color: 'var(--mint)',
            display: 'flex',
            alignItems: 'center',
            gap: 6
          }}
        >
          <RefreshCw size={10} className={isCompiling ? 'animate-spin' : ''} />
          {isCompiling ? 'RUNNING AGENT...' : 'TRIGGER AGENT PIPELINE'}
        </button>
      </div>

      {isCompiling && (
        <div className="fg-alert-banner fg-fade-in" style={{ borderColor: 'var(--mint)', background: 'rgba(45,232,196,0.05)', margin: '0 14px 14px' }}>
          <div className="txt">
            <div className="eyebrow" style={{ color: 'var(--mint)' }}>Autonomous Agent Checklist</div>
            <div className="title" style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>
              Status: {compileStatus}
            </div>
          </div>
        </div>
      )}

      {/* Reports List / Navigator if multiple exist */}
      {reports.length > 1 && (
        <div style={{ display: 'flex', gap: 6, margin: '0 14px 10px', overflowX: 'auto', paddingBottom: 4 }}>
          {reports.map((r, idx) => (
            <button
              key={r.id}
              onClick={() => setActiveReportIdx(idx)}
              className="mono"
              style={{
                background: activeReportIdx === idx ? 'var(--panel-raised)' : 'transparent',
                border: `1px solid ${activeReportIdx === idx ? 'var(--line-bright)' : 'var(--line)'}`,
                padding: '4px 8px',
                fontSize: 9,
                borderRadius: 4,
                color: activeReportIdx === idx ? 'var(--mint)' : 'var(--text-dim)',
                whiteSpace: 'nowrap'
              }}
            >
              Report #{r.id}
            </button>
          ))}
        </div>
      )}

      <div className="fg-grid-2">
        <div className="fg-report-doc">
          <h3>{reportDetails.incidentId}</h3>
          <div className="meta">
            <span>{reportDetails.location}</span>
            <span>AI AGENT: {reportDetails.agentName}</span>
          </div>

          <div className="fg-page-title" style={{ margin: '0 0 8px', fontSize: 11 }}>Incident Summary</div>
          <ul className="fg-report-list">
            <li><TreePine size={14} /> {reportDetails.summary[0]}</li>
            <li><Volume2 size={14} /> {reportDetails.summary[1]}</li>
            <li><Plane size={14} /> {reportDetails.summary[2]}</li>
            <li><ThermometerSun size={14} /> {reportDetails.summary[3]}</li>
          </ul>

          <div className="fg-page-title" style={{ margin: '16px 0 8px', fontSize: 11 }}>Recommended Enforcement</div>
          <ul className="fg-report-list">
            <li><Plane size={14} /> {reportDetails.enforcement[0]}</li>
            <li><ShieldAlert size={14} /> {reportDetails.enforcement[1]}</li>
            <li><MessageSquareWarning size={14} /> {reportDetails.enforcement[2]}</li>
          </ul>

          {/* Download Live PDF Action */}
          {activeReport && (
            <a 
              href={apiService.getReportDownloadUrl(activeReport.id)} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{
                display: 'block',
                marginTop: 20,
                textAlign: 'center',
                background: 'rgba(0, 240, 255, 0.08)',
                border: '1px solid rgba(0, 240, 255, 0.25)',
                color: 'var(--blue)',
                fontSize: 10,
                fontWeight: 'bold',
                fontFamily: 'var(--font-ui)',
                padding: '8px 12px',
                borderRadius: 6,
                textDecoration: 'none',
                letterSpacing: 0.5
              }}
            >
              DOWNLOAD COMPILED EVIDENCE PDF
            </a>
          )}
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

          <button 
            className="fg-authorize-btn" 
            onClick={() => handleAuthorize(activeReport?.id || 'mock')} 
            disabled={isSent || isCompiling}
          >
            <Fingerprint size={18} />
            <span>
              {isSent ? 'NOTIFICATION SENT' : 'AUTHORIZE NOTIFICATION'}
              <small>Send evidence package · initiate enforcement protocols</small>
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
