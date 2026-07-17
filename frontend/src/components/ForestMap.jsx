import React, { useState } from 'react';
import { Brain, Gauge } from 'lucide-react';

const BREACHES = [
  { id: 1, x: 30, y: 62, label: 'Sector 4-X (Low)', big: false },
  { id: 2, x: 46, y: 48, label: 'Sector 7-G (Critical)', big: true },
  { id: 3, x: 63, y: 58, label: 'Sector 2-C (Medium)', big: false },
  { id: 4, x: 58, y: 40, label: 'Sector 9-K (High)', big: false },
];

function BreachMarker({ x, y, label, big }) {
  return (
    <div
      className="dfn-breach"
      style={{ 
        left: `${x}%`, 
        top: `${y}%`,
        transform: 'translate3d(-50%, -50%, 25px)',
        transformStyle: 'preserve-3d'
      }}
    >
      <span className="dfn-breach-ring" style={big ? { width: 46, height: 46, borderColor: 'var(--alert)' } : { borderColor: 'var(--alert)' }} />
      <span className="dfn-breach-dot" style={{ background: 'var(--alert)', boxShadow: '0 0 10px 2px var(--alert)' }} />
      <span className="dfn-breach-label" style={{ borderColor: 'rgba(255, 180, 171, 0.3)' }}>{label}</span>
    </div>
  );
}

export default function ForestMap({ alerts = [], stats = null }) {
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Normalize coordinates: center is (0,0), edges are range [-0.5, 0.5]
    const normX = (x / rect.width) - 0.5;
    const normY = (y / rect.height) - 0.5;
    
    // Set rotation degrees (max 10 degrees tilt)
    setTilt({
      x: -normY * 10,
      y: normX * 10
    });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
  };

  // Bounding box for Amazon region: Lat -3.55 to -3.35, Lon -62.30 to -62.10
  const minLat = -3.55;
  const maxLat = -3.35;
  const minLon = -62.30;
  const maxLon = -62.10;

  const breaches = alerts.length > 0
    ? alerts.map((a, idx) => {
        const isCritical = a.risk_level === 'Critical';
        const label = `Sector ${a.id} (${a.risk_level || 'Unknown'})`;
        
        let x = 50;
        let y = 50;
        
        if (a.longitude >= minLon && a.longitude <= maxLon) {
          x = ((a.longitude - minLon) / (maxLon - minLon)) * 100;
        } else {
          // deterministic fallback distribution so they don't stack
          x = 20 + (idx * 27) % 60;
        }
        
        if (a.latitude >= minLat && a.latitude <= maxLat) {
          y = ((maxLat - a.latitude) / (maxLat - minLat)) * 100;
        } else {
          y = 30 + (idx * 17) % 50;
        }
        
        return {
          id: a.id,
          x,
          y,
          label,
          big: isCritical
        };
      })
    : BREACHES;

  let regionName = "AMAZON WILDLIFE RESERVE";
  let coordLabel = "3.46° S, 62.21° W";
  
  if (alerts.length > 0) {
    const firstAlert = alerts[0];
    if (firstAlert.region && firstAlert.region.name) {
      regionName = firstAlert.region.name.toUpperCase();
      
      try {
        const geom = typeof firstAlert.region.geometry === 'string' 
          ? JSON.parse(firstAlert.region.geometry) 
          : firstAlert.region.geometry;
          
        if (geom && geom.type === "Polygon" && geom.coordinates && geom.coordinates[0]) {
          const coords = geom.coordinates[0];
          let sumLat = 0;
          let sumLon = 0;
          // Polygon coordinates usually include the closing vertex, sum up all vertices
          coords.forEach(pt => {
            sumLon += pt[0];
            sumLat += pt[1];
          });
          const avgLat = sumLat / coords.length;
          const avgLon = sumLon / coords.length;
          
          const latStr = avgLat < 0 ? `${Math.abs(avgLat).toFixed(4)}° S` : `${avgLat.toFixed(4)}° N`;
          const lonStr = avgLon < 0 ? `${Math.abs(avgLon).toFixed(4)}° W` : `${avgLon.toFixed(4)}° E`;
          coordLabel = `${latStr}, ${lonStr}`;
        }
      } catch (e) {
        console.error("Error parsing region geometry:", e);
        // Fallback coordination checks
        if (regionName.includes("KALIMANTAN") || regionName.includes("SOUTHEAST ASIA") || firstAlert.longitude > 100) {
          coordLabel = "1.2500° S, 116.8900° E";
        } else {
          coordLabel = "3.4600° S, 62.2100° W";
        }
      }
    }
  }

  let avgConfidence = 98.4;
  if (alerts.length > 0) {
    const confidences = alerts.map(a => {
      if (a.ndvi_diff_mean) {
        return Math.min(Math.max(Math.round(Math.abs(a.ndvi_diff_mean) * 150), 60), 99);
      }
      return a.confidence === 'high' ? 95 : 75;
    });
    avgConfidence = Math.round((confidences.reduce((acc, curr) => acc + curr, 0) / confidences.length) * 10) / 10;
  }

  let agentState = 'STANDBY';
  let agentStateColor = 'var(--text-dim)';
  let activeSegments = 1;
  if (alerts.length > 0) {
    const hasCritical = alerts.some(a => a.risk_level === 'Critical');
    const hasHigh = alerts.some(a => a.risk_level === 'High');
    const hasPending = alerts.some(a => a.status === 'Pending');
    if (hasCritical) {
      agentState = 'CRITICAL';
      agentStateColor = 'var(--alert)';
      activeSegments = 5;
    } else if (hasHigh) {
      agentState = 'HIGH ALERT';
      agentStateColor = 'var(--amber)';
      activeSegments = 4;
    } else if (hasPending) {
      agentState = 'REASONING';
      agentStateColor = 'var(--mint)';
      activeSegments = 3;
    } else {
      agentState = 'NOMINAL';
      agentStateColor = 'var(--mint)';
      activeSegments = 2;
    }
  } else {
    // defaults for empty list
    agentState = 'REASONING';
    agentStateColor = 'var(--mint)';
    activeSegments = 3;
  }

  return (
    <div className="fg-panel dfn-map-panel fg-fade-in" style={{ padding: 12 }}>
      <div className="fg-taskid">
        <span>LIVE SATELLITE OVERLAY <b>· SECTOR 7 GRID</b></span>
        <span style={{ color: alerts.some(a => a.risk_level === 'Critical' || a.risk_level === 'High') ? 'var(--alert)' : 'var(--mint)' }}>
          ● {breaches.length} ACTIVE
        </span>
      </div>

      <div 
        className="dfn-map-frame"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{
          transform: `perspective(1000px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) scale3d(1.01, 1.01, 1.01)`,
          transition: 'transform 0.15s ease-out',
          transformStyle: 'preserve-3d',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
          position: 'relative'
        }}
      >
        <img 
          alt="Satellite Overlay" 
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuAGXOX6Cj7IQ3ml5XfKl2JOld8yJO-9LaVwkcLKTMQIJ5hGskfrWPoTDmHU_Gw-Zc0rGZZYM8jlHgwPx7Km3t3iOt8_RIh_ebBDQUpy2wtCyAvOKE7yKB00AdttN5Lu7Wz8dHNlifi1x8jtyvkVgzMxUL83_WhO7k9-hVvpoXjkM8UDGfQwhFYy5wQeEcWl60S8Y5PXsJDHf4JDhP0G9HKYgnG2iPpAZCvH5hyNc_yMjRczCPqJMYs_eRPxUVPjl40fjRcgmav6Ev9o"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.9,
            filter: 'brightness(85%) contrast(110%)',
            transform: 'translateZ(0px)'
          }}
        />

        {/* 3D Visual HUD Overlays */}
        <div className="dfn-map-grid-overlay" />
        <div className="hud-scanner" />

        {/* Floating Location Overlay */}
        <div 
          className="hud-glass"
          style={{
            position: 'absolute',
            top: 12,
            left: 12,
            padding: '6px 12px',
            borderRadius: 4,
            borderLeft: '2px solid var(--mint)',
            fontFamily: 'var(--font-mono)',
            fontSize: 9,
            color: 'var(--mint)',
            letterSpacing: '1px',
            transform: 'translate3d(0, 0, 35px)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            pointerEvents: 'none',
            zIndex: 20
          }}
        >
          <span style={{ opacity: 0.6 }}>LOC:</span>
          <span style={{ fontWeight: 'bold' }}>{regionName}</span>
          <span style={{ fontSize: 8, opacity: 0.5 }}>[{coordLabel}]</span>
        </div>

        {breaches.map((b) => <BreachMarker key={b.id || b.label} {...b} />)}

        <div 
          className="dfn-overlay-stats" 
          style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            gap: 8, 
            zIndex: 20,
            transform: 'translate3d(0, 0, 45px)'
          }}
        >
          {/* Agent State Chip */}
          <div className="hud-glass" style={{ padding: '8px 12px 8px 10px', borderRadius: 4, display: 'flex', flexDirection: 'column', gap: 2, borderLeft: '2px solid var(--mint)', borderTop: 'none', borderRight: 'none', borderBottom: 'none' }}>
            <div style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'rgba(145, 255, 226, 0.7)', trackingLetter: '1px', textTransform: 'uppercase' }}>Agent State</div>
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--mint)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Brain size={14} />
              {agentState}
            </div>
            {/* Segmented Progress Bar */}
            <div style={{ display: 'flex', gap: 2, marginTop: 4, width: '100%', minWidth: 80 }}>
              <div style={{ height: 4, flex: 1, background: 'var(--mint)', opacity: activeSegments >= 1 ? 1 : 0.2 }} />
              <div style={{ height: 4, flex: 1, background: 'var(--mint)', opacity: activeSegments >= 2 ? 1 : 0.2 }} />
              <div style={{ height: 4, flex: 1, background: 'var(--mint)', opacity: activeSegments >= 3 ? 1 : 0.2 }} />
              <div style={{ height: 4, flex: 1, background: 'var(--mint)', opacity: activeSegments >= 4 ? 1 : 0.2 }} />
              <div style={{ height: 4, flex: 1, background: 'var(--mint)', opacity: activeSegments >= 5 ? 1 : 0.2 }} />
            </div>
          </div>

          {/* Confidence Chip */}
          <div className="hud-glass" style={{ padding: '8px 12px 8px 10px', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, borderLeft: '2px solid var(--blue)', borderTop: 'none', borderRight: 'none', borderBottom: 'none' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <div style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'rgba(76, 214, 251, 0.7)', trackingLetter: '1px', textTransform: 'uppercase' }}>Confidence</div>
              <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--blue)' }}>{avgConfidence}%</div>
            </div>
            {/* Circular Gauge placeholder */}
            <div style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              border: '2px solid rgba(76, 214, 251, 0.3)',
              borderTopColor: 'var(--blue)',
              borderRightColor: 'var(--blue)',
              transform: 'rotate(45deg)',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transform: 'rotate(-45deg)',
                fontSize: 9,
                fontFamily: 'var(--font-mono)',
                color: 'var(--blue)'
              }}>
                {Math.round(avgConfidence)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
