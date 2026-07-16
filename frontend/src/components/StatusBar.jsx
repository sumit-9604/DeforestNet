import React, { useEffect, useState } from 'react';
import { Radio } from 'lucide-react';

export default function StatusBar() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const utc = time.toISOString().slice(11, 19);

  return (
    <div className="fg-statusbar">
      <span className="ticker-item"><span className="dot" /> System nominal</span>
      <span className="ticker-item mono">{utc} UTC</span>
      <span className="ticker-item"><Radio size={12} /> Uplink stable</span>
    </div>
  );
}
