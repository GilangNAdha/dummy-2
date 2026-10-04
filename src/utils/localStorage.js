// kf = keluargafin config object
export const kf = {
  failMode: false, // ubah ke true untuk simulasi localStorage gagal (QA testing)
};

export function save(key, data) {
  if (kf.failMode) {
    console.warn('[localStorage] failMode aktif — save diabaikan:', key);
    return;
  }
  try {
    localStorage.setItem(key, JSON.stringify(data));
    console.log('[localStorage] save:', key, data);
  } catch (e) {
    console.error('[localStorage] Gagal save:', key, e);
  }
}

export function load(key, fallback = null) {
  if (kf.failMode) {
    console.warn('[localStorage] failMode aktif — load diabaikan:', key);
    return fallback;
  }
  try {
    const raw = localStorage.getItem(key);
    const result = raw ? JSON.parse(raw) : fallback;
    console.log('[localStorage] load:', key, result);
    return result;
  } catch (e) {
    console.error('[localStorage] Gagal load:', key, e);
    return fallback;
  }
}

export function clear(key) {
  localStorage.removeItem(key);
  console.log('[localStorage] clear:', key);
}
