// ToastContext — global feedback system
// Pakai: const { showToast } = useToast(); showToast('Berhasil!', 'success');

import { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠️' };
const styles = {
  success: { bg: '#0F172A', color: '#fff',    border: '#1E293B' },
  error:   { bg: '#EF4444', color: '#fff',    border: '#DC2626' },
  info:    { bg: '#3B82F6', color: '#fff',    border: '#2563EB' },
  warning: { bg: '#F59E0B', color: '#fff',    border: '#D97706' },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'success', duration = 3000) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const dismiss = (id) => setToasts(prev => prev.filter(t => t.id !== id));

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}

      {/* Toast stack — pojok kanan bawah */}
      <div className="fixed bottom-24 right-4 lg:bottom-6 lg:right-6 z-[100] flex flex-col gap-2 items-end">
        {toasts.map(t => {
          const s = styles[t.type] ?? styles.success;
          return (
            <div key={t.id}
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium max-w-xs shadow-lg"
              style={{
                backgroundColor: s.bg,
                color: s.color,
                border: `1px solid ${s.border}`,
                animation: 'slideIn 0.2s ease-out',
              }}>
              <span className="shrink-0 font-bold">{icons[t.type]}</span>
              <span className="flex-1">{t.message}</span>
              <button onClick={() => dismiss(t.id)}
                className="shrink-0 opacity-60 hover:opacity-100 transition-opacity ml-1">
                ×
              </button>
            </div>
          );
        })}
      </div>

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(16px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast harus dipakai di dalam ToastProvider');
  return ctx;
}
