import React, { useEffect, useState } from 'react';
import { Radio } from 'lucide-react';

export default function StatusBar() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const ist = time.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Kolkata'
  });

  return (
    <div className="fg-statusbar">
      <span className="ticker-item"><span className="dot" /> System nominal</span>
      <span className="ticker-item mono">{ist} IST</span>
      <span className="ticker-item"><Radio size={12} /> Uplink stable</span>
    </div>
  );
}
