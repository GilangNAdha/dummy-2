// getData.js — lapisan data fetching
//
// Dua jalan data:
//   1. Jalan API   — dompet dan kategori sudah tersambung ke endpoint FastAPI
//      lewat src/API/apiClient.js. Aktif bila VITE_API_URL, token sesi, dan
//      id rumah tangga tersedia.
//   2. Jalan lokal — localStorage dengan fallback ke mockData (mode demo,
//      dipakai saat backend belum dinyalakan dan untuk materi kuliah).

import { load, save } from '../utils/localStorage';
import { track } from '../utils/analytics';
import { apiAktif, panggil, rumahTanggaId } from './apiClient';
import {
  accountFromApi,
  accountToApi,
  categoryFromApi,
  categoryToApi,
  createLookups,
  withHousehold,
  FIELD_MAP,
} from './adapters';
import {
  transactions as mockTransactions,
  budgets as mockBudgets,
  goals as mockGoals,
  categories as mockCategories,
  mockAccounts,
} from '../data/mockData';

// Alamat API lengkap ada di apiClient.js (VITE_API_URL, bawaan /api/v1)

// ─── Transactions ────────────────────────────────────────────

export async function getTransactions() {
  track('getData:getTransactions');

  // Nanti ganti dengan:
  // const { data } = await axios.get(`${BASE_URL}/transactions`);
  // return data;

  const cached = load('kf_transactions', null);
  if (cached) return cached;

  await simulateDelay();
  save('kf_transactions', mockTransactions);
  return mockTransactions;
}

export async function postTransaction(txn) {
  track('getData:postTransaction', { merchant: txn.merchant, amount: txn.amount });

  // Nanti ganti dengan:
  // const { data } = await axios.post(`${BASE_URL}/transactions`, txn);
  // return data;

  const current = load('kf_transactions', mockTransactions);
  const updated = [txn, ...current];
  save('kf_transactions', updated);
  return txn;
}

// ─── Budgets ─────────────────────────────────────────────────

export async function getBudgets() {
  track('getData:getBudgets');

  // Nanti ganti dengan:
  // const { data } = await axios.get(`${BASE_URL}/budgets`);
  // return data;

  const cached = load('kf_budgets', null);
  if (cached) return cached;

  await simulateDelay();
  save('kf_budgets', mockBudgets);
  return mockBudgets;
}

export async function putBudget(category, limit) {
  track('getData:putBudget', { category, limit });

  // Nanti ganti dengan:
  // const { data } = await axios.put(`${BASE_URL}/budgets/${category}`, { limit });
  // return data;

  const current = load('kf_budgets', mockBudgets);
  const updated = current.map(b => b.category === category ? { ...b, limit } : b);
  save('kf_budgets', updated);
  return updated;
}

// ─── Goals ───────────────────────────────────────────────────

export async function getGoals() {
  track('getData:getGoals');

  // Nanti ganti dengan:
  // const { data } = await axios.get(`${BASE_URL}/goals`);
  // return data;

  const cached = load('kf_goals', null);
  if (cached) return cached;

  await simulateDelay();
  save('kf_goals', mockGoals);
  return mockGoals;
}

export async function postGoalContribution(goalId, amount) {
  track('getData:postGoalContribution', { goalId, amount });

  // Nanti ganti dengan:
  // const { data } = await axios.post(`${BASE_URL}/goals/${goalId}/contribute`, { amount });
  // return data;

  const current = load('kf_goals', mockGoals);
  const updated = current.map(g =>
    g.id === goalId ? { ...g, current: Math.min(g.current + amount, g.target) } : g
  );
  save('kf_goals', updated);
  return updated;
}

// ─── Categories ──────────────────────────────────────────────

export async function getCategories() {
  track('getData:getCategories');

  // Jalan API: GET /api/v1/categories. Kategori sistem (household_id kosong)
  // ikut terbaca semua rumah tangga, jadi delapan kategori bawaan selalu ada.
  if (apiAktif()) {
    const jawaban = await panggil('/categories', {
      params: { household_id: rumahTanggaId(), per_page: 100 },
    });
    return (jawaban?.data ?? []).map(categoryFromApi);
  }

  const cached = load('kf_categories', null);
  if (cached) return cached;

  await simulateDelay();
  save('kf_categories', mockCategories);
  return mockCategories;
}

export async function postCategory(cat) {
  track('getData:postCategory', { name: cat.name });

  // Jalan API: POST /api/v1/categories. Server yang memaksa is_system = false;
  // nama yang sama dengan kategori sistem dijawab 409 oleh backend.
  if (apiAktif()) {
    const lookups = createLookups({ household: { id: rumahTanggaId() } });
    const isi = withHousehold(categoryToApi(cat), lookups);
    const jawaban = await panggil('/categories', { method: 'POST', body: isi });
    return categoryFromApi(jawaban.data);
  }

  const current = load('kf_categories', mockCategories);
  const updated = [...current, cat];
  save('kf_categories', updated);
  return updated;
}

export async function putCategory(name, changes) {
  track('getData:putCategory', { name });

  // Jalan API: PATCH /api/v1/categories/{id}. Antarmuka memakai nama sebagai
  // kunci, sedangkan kontrak memakai id, jadi id dicari dari daftar dulu
  // lewat createLookups (panduan kerja langkah 13).
  if (apiAktif()) {
    const lookups = createLookups({ categories: await getCategories() });
    const id = lookups.resolveCategoryId(name);
    const isi = {};
    if (changes.name !== undefined) isi.name = changes.name;
    if (changes.kind !== undefined) isi.kind = changes.kind;
    if (changes.icon !== undefined) isi.icon = changes.icon;
    if (changes.color !== undefined) isi.color = changes.color;
    if (changes.archived !== undefined) isi[FIELD_MAP.category.archived] = changes.archived;
    const jawaban = await panggil(`/categories/${id}`, { method: 'PATCH', body: isi });
    return categoryFromApi(jawaban.data);
  }

  const current = load('kf_categories', mockCategories);
  const updated = current.map(c => c.name === name ? { ...c, ...changes } : c);
  save('kf_categories', updated);
  return updated;
}

// ─── Accounts ────────────────────────────────────────────────

export async function getAccounts() {
  track('getData:getAccounts');

  // Jalan API: GET /api/v1/accounts (per_page 100 cukup untuk 3 sampai 20 baris)
  if (apiAktif()) {
    const jawaban = await panggil('/accounts', {
      params: { household_id: rumahTanggaId(), per_page: 100 },
    });
    // map → ubah baris backend (snake_case) menjadi bentuk antarmuka
    return (jawaban?.data ?? []).map(accountFromApi);
  }

  // Jalan lokal (mode demo)
  const cached = load('kf_accounts', null);
  if (cached) return cached;

  await simulateDelay();
  save('kf_accounts', mockAccounts);
  return mockAccounts;
}

export async function postAccount(acc) {
  track('getData:postAccount', { name: acc.name });

  // Jalan API: POST /api/v1/accounts, saldo awal dikirim saat pembuatan
  if (apiAktif()) {
    const lookups = createLookups({ household: { id: rumahTanggaId() } });
    const isi = withHousehold(accountToApi(acc), lookups);
    const jawaban = await panggil('/accounts', { method: 'POST', body: isi });
    return accountFromApi(jawaban.data);
  }

  const current = load('kf_accounts', mockAccounts);
  const updated = [...current, acc];
  save('kf_accounts', updated);
  return updated;
}

export async function putAccount(id, changes) {
  track('getData:putAccount', { id });

  // Jalan API: PATCH /api/v1/accounts/{id}, hanya kolom yang berubah.
  // Nama field mengikuti kamus FIELD_MAP pada adapters.js.
  if (apiAktif()) {
    const isi = {};
    if (changes.name !== undefined) isi.name = changes.name;
    if (changes.type !== undefined) isi.type = changes.type;
    if (changes.provider !== undefined) isi.provider = changes.provider;
    if (changes.balance !== undefined) {
      isi[FIELD_MAP.account.balance] = Number(String(changes.balance).replace(/\D/g, '')) || 0;
    }
    if (changes.isActive !== undefined) isi.is_active = changes.isActive;
    const jawaban = await panggil(`/accounts/${id}`, { method: 'PATCH', body: isi });
    return accountFromApi(jawaban.data);
  }

  const current = load('kf_accounts', mockAccounts);
  const updated = current.map(a => a.id === id ? { ...a, ...changes } : a);
  save('kf_accounts', updated);
  return updated;
}

export async function deleteAccount(id) {
  track('getData:deleteAccount', { id });

  // Jalan API: DELETE /api/v1/accounts/{id}. Bila dompet masih dipakai
  // transaksi, backend menjawab 409 dan pesannya dibaca dari error.message
  // oleh pemanggil (Settings memakai useToast).
  if (apiAktif()) {
    return await panggil(`/accounts/${id}`, { method: 'DELETE' });
  }

  const current = load('kf_accounts', mockAccounts);
  const updated = current.filter(a => a.id !== id);
  save('kf_accounts', updated);
  return updated;
}

// ─── Helper ──────────────────────────────────────────────────

function simulateDelay(ms = 400) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
