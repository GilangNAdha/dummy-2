
import { useState, useEffect } from 'react';
import { track } from '../utils/analytics';

export function useFetch(fetchFn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [trigger, setTrigger] = useState(0);

  // refetch() → panggil ini untuk fetch ulang tanpa reload halaman
  const refetch = () => setTrigger(t => t + 1);

  useEffect(() => {
    let cancelled = false; // hindari state update setelah komponen unmount

    setLoading(true);
    setError(null);

    fetchFn()
      .then(result => {
        if (cancelled) return;
        setData(result);
        track('useFetch:success', { count: Array.isArray(result) ? result.length : 1 });
      })
      .catch(err => {
        if (cancelled) return;
        setError(err.message ?? 'Terjadi kesalahan');
        track('useFetch:error', { message: err.message });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    // cleanup: batalkan jika deps berubah sebelum fetch selesai
    return () => { cancelled = true; };

  }, [...deps, trigger]); // trigger memicu refetch manual

  return { data, loading, error, refetch };
}
