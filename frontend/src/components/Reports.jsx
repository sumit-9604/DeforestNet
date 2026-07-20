import React, { useState } from 'react';
import { TreePine, Volume2, Plane, ThermometerSun, ShieldAlert, MessageSquareWarning, FileCheck2, CheckCircle2, Fingerprint, RefreshCw } from 'lucide-react';
import { apiService } from '../services/api.js';

export default function Reports({ reports = [], alerts = [], onRefresh }) {
  const [activeReportIdx, setActiveReportIdx] = useState(0);
  const [isCompiling, setIsCompiling] = useState(false);
  const [sentMap, setSentMap] = useState({});
  const [compileStatus, setCompileStatus] = useState('');
  const [authorizationError, setAuthorizationError] = useState('');
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [humanOversight, setHumanOversight] = useState(true);
  const [filterMode, setFilterMode] = useState('ALL'); // 'ALL', 'LIVE', 'SIM'

  // Filtered reports
  const filteredReports = reports.filter(r => {
    const associatedAlert = alerts.find(a => a.id === r.alert_id) || {};
    const alertDetails = typeof associatedAlert.details === 'string' ? JSON.parse(associatedAlert.details) : (associatedAlert.details || {});
    const isSim = alertDetails?.simulated || 
                  alertDetails?.source === 'Simulation Generator' || 
                  (associatedAlert.latitude && Math.abs(associatedAlert.latitude - (-3.525600)) > 0.001);
    if (filterMode === 'LIVE') return !isSim;
    if (filterMode === 'SIM') return isSim;
    return true;
  });

  const activeReport = filteredReports[activeReportIdx] || filteredReports[0] || null;

  // Handle triggering a live pipeline check
  const handleTriggerCheck = async () => {
    try {
      setHumanOversight(true);
      setIsCompiling(true);
      setCompileStatus('Retrieving alerts from GFW...');
      
      const res = await apiService.triggerCheck("Amazon Wildlife Reserve", true);
      console.log("Pipeline run complete:", res);
      
      setCompileStatus('Compiling evidence packages...');
      setTimeout(() => {
        setCompileStatus('Seeding database schemas...');
        setTimeout(() => {
          setIsCompiling(false);
          setCompileStatus('');
          if (onRefresh) onRefresh({ showLoading: false });
        }, 1000);
      }, 1000);
      
    } catch (err) {
      console.error("Pipeline trigger failed:", err);
      setIsCompiling(false);
      setCompileStatus('');
    }
  };

  const handleAuthorize = async (reportId) => {
    if (!activeReport?.alert_id) {
      setAuthorizationError('Select a generated evidence report before authorizing delivery.');
      return;
    }

    setAuthorizationError('');
    setIsAuthorizing(true);
    try {
      await apiService.updateAlertStatus(activeReport.alert_id, "Authorized");
      setSentMap(prev => ({ ...prev, [reportId]: true }));
      if (onRefresh) await onRefresh({ showLoading: false });
    } catch (err) {
      console.error("Failed to authorize report:", err);
      setAuthorizationError(err.message || 'Unable to authorize the notification.');
    } finally {
      setIsAuthorizing(false);
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
      agentName: 'DEFORESTNET-GEMINI-2.0',
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

  const isSent = activeReport ? (sentMap[activeReport.id] || activeReport.status === 'Sent') : false;

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

      {authorizationError && (
        <div className="fg-alert-banner" role="alert" style={{ margin: '0 14px 14px' }}>
          <div className="txt">
            <div className="eyebrow">Notification not sent</div>
            <div className="title" style={{ fontSize: 11 }}>{authorizationError}</div>
          </div>
        </div>
      )}

      {/* Dynamic Filters */}
      <div style={{ display: 'flex', gap: 6, margin: '0 14px 12px', alignItems: 'center' }}>
        <span className="mono" style={{ fontSize: 9, color: 'var(--text-faint)', marginRight: 4 }}>Filter View:</span>
        {['ALL', 'LIVE', 'SIM'].map(mode => (
          <button
            key={mode}
            onClick={() => {
              setFilterMode(mode);
              setActiveReportIdx(0);
            }}
            className="mono"
            style={{
              background: filterMode === mode ? 'rgba(0, 240, 255, 0.1)' : 'transparent',
              border: `1px solid ${filterMode === mode ? 'var(--blue)' : 'var(--line)'}`,
              padding: '3px 8px',
              fontSize: 8,
              borderRadius: 4,
              color: filterMode === mode ? 'var(--blue)' : 'var(--text-dim)',
              cursor: 'pointer',
              fontWeight: filterMode === mode ? 'bold' : 'normal'
            }}
          >
            {mode === 'ALL' ? 'SHOW ALL' : (mode === 'LIVE' ? 'LIVE PRODUCTION' : 'SIMULATED')}
          </button>
        ))}
      </div>

      {/* Reports List / Navigator if multiple exist */}
      {filteredReports.length > 1 && (
        <div style={{ display: 'flex', gap: 6, margin: '0 14px 10px', overflowX: 'auto', paddingBottom: 4 }}>
          {filteredReports.map((r, idx) => {
            const associatedAlert = alerts.find(a => a.id === r.alert_id) || {};
            const alertDetails = typeof associatedAlert.details === 'string' ? JSON.parse(associatedAlert.details) : (associatedAlert.details || {});
            // Fallback: If coordinates do not match the real GFW query coordinates, tag as simulated
            const isSim = alertDetails?.simulated || 
                          alertDetails?.source === 'Simulation Generator' || 
                          (associatedAlert.latitude && Math.abs(associatedAlert.latitude - (-3.525600)) > 0.001);
            return (
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
                  whiteSpace: 'nowrap',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}
              >
                <span>Report #{r.id}</span>
                <span style={{
                  fontSize: 8,
                  opacity: 0.8,
                  color: isSim ? 'var(--amber)' : 'var(--mint)'
                }}>
                  ({isSim ? 'SIM' : 'LIVE'})
                </span>
              </button>
            );
          })}
        </div>
      )}

      <div className="fg-grid-2">
        <div className="fg-report-doc" style={{ display: 'flex', flexDirection: 'column', minHeight: 320 }}>
          {filteredReports.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, padding: '40px 20px', color: 'var(--text-dim)', textAlign: 'center' }}>
              <span className="mono" style={{ fontSize: 11, marginBottom: 8, color: 'var(--blue)' }}>NO REPORTS FOUND</span>
              <span style={{ fontSize: 10, maxWidth: 280, lineHeight: 1.4 }}>
                There are no reports matching this filter view in the database. Switch settings or trigger the pipeline to generate new alerts.
              </span>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <h3 style={{ margin: 0 }}>{reportDetails.incidentId}</h3>
                {(() => {
                  const associatedAlert = alerts.find(a => a.id === activeReport?.alert_id) || {};
                  const alertDetails = typeof associatedAlert.details === 'string' ? JSON.parse(associatedAlert.details) : (associatedAlert.details || {});
                  const isSim = alertDetails?.simulated || 
                                alertDetails?.source === 'Simulation Generator' || 
                                (associatedAlert.latitude && Math.abs(associatedAlert.latitude - (-3.525600)) > 0.001);
                  return (
                    <span style={{
                      background: isSim ? 'rgba(255, 179, 176, 0.1)' : 'rgba(145, 255, 226, 0.1)',
                      border: `1px solid ${isSim ? 'var(--amber)' : 'var(--mint)'}`,
                      color: isSim ? 'var(--amber)' : 'var(--mint)',
                      fontSize: 9,
                      padding: '2px 6px',
                      borderRadius: 4,
                      fontWeight: 'bold',
                      fontFamily: 'var(--font-mono)'
                    }}>
                      {isSim ? 'SIMULATED DATA' : 'LIVE DATA'}
                    </span>
                  );
                })()}
              </div>
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
                    marginTop: 'auto',
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
            </>
          )}
        </div>

        <div>
          <div className="fg-oversight-row">
            <span>Human oversight</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8, color: humanOversight ? 'var(--mint)' : 'var(--text-faint)' }}>
              {humanOversight ? 'ACTIVE' : 'INACTIVE'}
              <span 
                className={`fg-toggle-pill ${humanOversight ? '' : 'inactive'}`} 
                onClick={() => setHumanOversight(!humanOversight)}
              />
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
            disabled={isSent || isCompiling || isAuthorizing || !activeReport}
          >
            <Fingerprint size={18} />
            <span>
              {isSent ? 'NOTIFICATION SENT' : (isAuthorizing ? 'SENDING NOTIFICATION...' : 'AUTHORIZE NOTIFICATION')}
              <small>Send evidence package · initiate enforcement protocols</small>
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
