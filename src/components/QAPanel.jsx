// QaPanel.jsx — komponen React, masuk components/ bukan utils/

import { useState } from 'react';
import { getLogs } from '../utils/analytics';

export default function QAPanel() {
  const [open, setOpen] = useState(false);
  const [entries, setEntries] = useState([]);

  const refresh = () => setEntries(getLogs());

  if (!open) {
    return (
      <button
        onClick={() => { setOpen(true); refresh(); }}
        className="fixed bottom-20 right-4 lg:bottom-4 z-50 px-3 py-1.5 rounded-lg text-xs font-mono font-bold text-white"
        style={{ backgroundColor: '#7C3AED' }}
      >
        QA
      </button>
    );
  }

  return (
    <div
      className="fixed bottom-20 right-4 lg:bottom-4 z-50 w-80 rounded-xl overflow-hidden"
      style={{ boxShadow: 'rgba(0,0,0,0.3) 0px 16px 40px -8px' }}
    >
      <div className="flex items-center justify-between px-3 py-2" style={{ backgroundColor: '#7C3AED' }}>
        <span className="text-white text-xs font-mono font-bold">QA Panel — Analytics Log</span>
        <div className="flex gap-2">
          <button onClick={refresh} className="text-white/70 hover:text-white text-xs font-mono">↻</button>
          <button onClick={() => setOpen(false)} className="text-white/70 hover:text-white text-xs font-mono">×</button>
        </div>
      </div>
      <div className="bg-slate-900 max-h-64 overflow-y-auto p-3 space-y-1.5">
        {entries.length === 0 ? (
          <p className="text-slate-500 text-xs font-mono">Belum ada log. Coba interaksi dulu.</p>
        ) : [...entries].reverse().map((e, i) => (
          <div key={i} className="border-b border-slate-800 pb-1.5 last:border-0">
            <div className="flex items-center gap-2">
              <span className="text-slate-500 text-[10px] font-mono">{e.time}</span>
              <span className="text-violet-400 text-xs font-mono font-bold">{e.event}</span>
            </div>
            {Object.keys(e.data).length > 0 && (
              <pre className="text-slate-400 text-[10px] font-mono mt-0.5 whitespace-pre-wrap">
                {JSON.stringify(e.data, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
