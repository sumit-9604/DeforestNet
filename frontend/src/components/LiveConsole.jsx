import React, { useEffect, useRef, useState } from 'react';

const LOG_POOL = [
  'SENTINEL-2 :: GET /data/LIC/T44SNC/2026-07-16 200 OK',
  'DB :: QUERY land_registry WHERE parcel_id="9120-A" [42ms]',
  'AI_CORE :: process_anomaly_detect(spectral) -> conf=0.88',
  'NET :: tunnel to 192.168.1.55:443 established',
  'AGENT :: task 0x4F7B2A1E status -> IN_PROGRESS (68%)',
  'AUTH :: 2FA challenge sent to registry endpoint',
  'DRONE :: squadron_alpha telemetry sync ok',
  'SYS :: cpu 32% · mem 4.2GB · throughput 250Mbps',
];

export default function LiveConsole({ lines }) {
  const bodyRef = useRef(null);
  const [log, setLog] = useState([]);
  const prevLinesRef = useRef([]);

  // 1. Initial mount load
  useEffect(() => {
    if (lines && lines.length > 0) {
      setLog(lines);
      prevLinesRef.current = lines;
    } else {
      const initialLogs = LOG_POOL.slice(0, 4).map(l => {
        const time = new Date().toTimeString().slice(0, 8);
        return `${time} - ${l}`;
      });
      setLog(initialLogs);
      prevLinesRef.current = [];
    }
  }, []);

  // 2. Safely append new real database log events when they arrive, without overwriting existing logs
  useEffect(() => {
    if (!lines || lines.length === 0) return;
    
    // Find any new lines that aren't in our previous list
    const addedLines = lines.filter(l => !prevLinesRef.current.includes(l));
    if (addedLines.length > 0) {
      setLog(prev => [...prev, ...addedLines].slice(-20)); // keep last 20 lines
    }
    prevLinesRef.current = lines;
  }, [lines]);

  // 3. Append active background simulated ticks
  useEffect(() => {
    const iv = setInterval(() => {
      setLog((prev) => {
        const next = LOG_POOL[Math.floor(Math.random() * LOG_POOL.length)];
        const time = new Date().toTimeString().slice(0, 8);
        return [...prev.slice(-19), `${time} - ${next}`];
      });
    }, 3000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [log]);

  return (
    <div className="fg-console">
      <div className="fg-console-head">
        <span className="dot" style={{ background: '#ff5559' }} />
        <span className="dot" style={{ background: '#ffb54d' }} />
        <span className="dot" style={{ background: '#2de8c4' }} />
        <span style={{ marginLeft: 6 }}>LIVE CONSOLE — AGENT REASONING TRACE</span>
      </div>
      <div className="fg-console-body" ref={bodyRef}>
        {log.map((l, i) => (
          <div key={i}>
            <span className="ts">[{String(i + 1).padStart(2, '0')}]</span> {l}
          </div>
        ))}
        <span className="fg-console-cursor" />
      </div>
    </div>
  );
}
