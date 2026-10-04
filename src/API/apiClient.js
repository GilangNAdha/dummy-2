// apiClient.js — penghubung frontend ke layanan FastAPI (potongan dompet dan kategori)
//
// Aturan kontrak yang dipakai di sini (panduan kerja langkah 13):
//   - alamat dasar /api/v1, diatur lewat VITE_API_URL
//   - setiap permintaan membawa header Authorization: Bearer <token Supabase>
//   - galat dibaca dalam satu bentuk: error.code dan error.message
//   - token dan id rumah tangga disimpan di localStorage oleh halaman masuk
//     (AuthPage) saat integrasi Supabase Auth dikerjakan
//
// Selama VITE_API_URL belum diisi, lapisan ini dianggap tidak aktif dan
// getData.js memakai localStorage seperti mode demo sekarang. Dengan begitu
// demo tetap jalan tanpa backend, dan integrasi bisa dinyalakan bertahap.
import { load, save, clear } from '../utils/localStorage';
import { track } from '../utils/analytics';

const BASE_URL = (import.meta.env?.VITE_API_URL ?? '').replace(/\/$/, '');

const KUNCI_TOKEN = 'kf_access_token';
const KUNCI_RUMAH = 'kf_household_id';

export function simpanToken(token) {
  save(KUNCI_TOKEN, token);
}

export function ambilToken() {
  return load(KUNCI_TOKEN, null);
}

export function hapusToken() {
  clear(KUNCI_TOKEN);
}

export function simpanRumahTangga(id) {
  save(KUNCI_RUMAH, id);
}

export function rumahTanggaId() {
  return load(KUNCI_RUMAH, null) ?? load('kf_household', null)?.id ?? null;
}

/** true bila alamat API, token, dan id rumah tangga tersedia. */
export function apiAktif() {
  return Boolean(BASE_URL && ambilToken() && rumahTanggaId());
}

export function modeData() {
  return apiAktif() ? 'api' : 'lokal';
}

class GalatApi extends Error {
  constructor({ code, message, status, requestId }) {
    super(message);
    this.name = 'GalatApi';
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

function bangunQuery(params = {}) {
  const isi = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
  if (isi.length === 0) return '';
  return '?' + isi.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');
}

/**
 * Panggil satu endpoint. Mengembalikan badan jawaban (sudah diurai) atau
 * melempar GalatApi dengan code dan message dari backend.
 */
export async function panggil(path, { method = 'GET', body, params } = {}) {
  const alamat = `${BASE_URL}${path}${bangunQuery(params)}`;
  track('apiClient:panggil', { method, path, mode: modeData() });

  let res;
  try {
    res = await fetch(alamat, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${ambilToken()}`,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (e) {
    // backend mati atau jaringan putus
    track('apiClient:gagalJaringan', { path, message: e.message });
    throw new GalatApi({
      code: 'NETWORK_ERROR',
      message: 'Tidak bisa menghubungi layanan. Data yang tampil mungkin data terakhir yang tersimpan.',
      status: 0,
    });
  }

  const teks = await res.text();
  const isi = teks ? JSON.parse(teks) : null;

  if (!res.ok) {
    const galat = isi?.error ?? {};
    track('apiClient:gagal', { path, status: res.status, code: galat.code });
    throw new GalatApi({
      code: galat.code ?? 'HTTP_ERROR',
      message: galat.message ?? `Permintaan gagal (${res.status}).`,
      status: res.status,
      requestId: galat.request_id ?? res.headers.get('X-Request-Id'),
    });
  }

  return isi;
}
