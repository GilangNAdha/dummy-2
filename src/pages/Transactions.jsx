// Alur data: Transactions (luar fetch) → getTransactions → localStorage → tampilan

import { useState } from 'react';
import { useFetch } from '../hooks/useFetch';
import { getTransactions, postTransaction, getCategories } from '../API/getData';
import { track } from '../utils/analytics';
import { useToast } from '../context/ToastContext';
import { members, accounts, formatRupiah, formatDate } from '../data/mockData';
import Card from '../components/Card';
import Button from '../components/Button';

const typeColors  = { expense: '#EF4444', income: '#10B981', transfer: '#3B82F6' };
const typeLabels  = { expense: 'Pengeluaran', income: 'Pemasukan', transfer: 'Transfer' };
const filterChips = ['all', 'expense', 'income', 'transfer'];

const statusConfig = {
  selesai:  { label: 'Selesai',  bg: '#D1FAE5', color: '#065F46' },
  pending:  { label: 'Pending',  bg: '#FEF3C7', color: '#92400E' },
  dibatalkan: { label: 'Dibatalkan', bg: '#FEE2E2', color: '#991B1B' },
};

const emptyForm = {
  date: new Date().toISOString().split('T')[0],
  type: 'expense',
  amount: '',
  category: '',
  member: members[0],
  merchant: '',
  notes: '',
  account: accounts[0],
  status: 'selesai',
};

// Cek duplikat: merchant sama + jumlah sama + tanggal sama
function findDuplicate(txns, form) {
  const amt = parseInt(form.amount.replace(/\D/g, ''), 10) || 0;
  return txns.find(t =>
    t.date === form.date &&
    t.merchant.toLowerCase() === form.merchant.toLowerCase() &&
    t.amount === amt
  );
}

export default function Transactions() {
  const { showToast } = useToast();
  const { data: categoriesData } = useFetch(getCategories);
  const categories = (categoriesData ?? []).filter(c => !c.archived);

  const [filter, setFilter]           = useState('all');
  const [memberFilter, setMemberFilter] = useState('all');
  const [showForm, setShowForm]       = useState(false);
  const [form, setForm]               = useState(emptyForm);
  const [submitting, setSubmitting]   = useState(false);
  const [dupWarning, setDupWarning]   = useState(null); // transaksi duplikat yg ditemukan
  const [forceSave, setForceSave]     = useState(false); // user pilih tetap simpan

  const { data: transactions, loading, error, refetch } = useFetch(getTransactions);

  track('Transactions:render', { filter, memberFilter });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-slate-200 border-t-slate-800 rounded-full animate-spin" />
      </div>
    );
  }

  if (error) return <Card><p className="text-red-500 text-sm">⚠️ {error}</p></Card>;

  const txns = transactions ?? [];

  const filtered = txns
    .filter(t => (filter === 'all' || t.type === filter) && (memberFilter === 'all' || t.member === memberFilter))
    .sort((a, b) => b.date.localeCompare(a.date));

  // Set kategori default saat categories pertama kali load
  const defaultCat = categories[0]?.name ?? '';

  // Setiap kali form berubah → reset duplikat state
  const updateForm = (changes) => {
    setForm(prev => ({ ...prev, ...changes }));
    setDupWarning(null);
    setForceSave(false);
  };

  const handleAdd = async (e) => {
    e.preventDefault();

    // cek duplikat sebelum simpan (kecuali user sudah konfirmasi)
    if (!forceSave && form.merchant && form.amount) {
      const dup = findDuplicate(txns, form);
      if (dup) {
        track('Transactions:duplicateDetected', { merchant: form.merchant });
        setDupWarning(dup);
        return;
      }
    }

    setSubmitting(true);
    const newTxn = {
      id: String(Date.now()),
      ...form,
      amount: parseInt(form.amount.replace(/\D/g, ''), 10) || 0,
    };

    track('Transactions:addTransaction', { type: newTxn.type, amount: newTxn.amount, status: newTxn.status });

    await postTransaction(newTxn);
    refetch();
    showToast('Transaksi berhasil disimpan');
    setShowForm(false);
    setForm(emptyForm);
    setDupWarning(null);
    setForceSave(false);
    setSubmitting(false);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setForm(emptyForm);
    setDupWarning(null);
    setForceSave(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Keuangan</p>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Transaksi</h1>
        </div>
        <Button onClick={() => { track('Transactions:openForm'); setShowForm(true); }}>
          + Tambah Transaksi
        </Button>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2 items-center">
        <div className="flex bg-white rounded-xl p-1 border border-slate-100 gap-1">
          {filterChips.map((f) => (
            <button key={f}
              onClick={() => { track('Transactions:filter', { value: f }); setFilter(f); }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={{
                backgroundColor: filter === f ? '#0F172A' : 'transparent',
                color: filter === f ? '#fff' : '#64748B',
              }}>
              {f === 'all' ? 'Semua' : typeLabels[f]}
            </button>
          ))}
        </div>
        <select value={memberFilter}
          onChange={e => setMemberFilter(e.target.value)}
          className="px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-700 bg-white outline-none">
          <option value="all">Semua Anggota</option>
          {members.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {/* Daftar transaksi */}
      <Card padding="p-0" className="overflow-hidden">
        {filtered.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-2xl mb-2">📭</p>
            <p className="text-sm text-slate-400">Tidak ada transaksi ditemukan.</p>
          </div>
        ) : (
          filtered.map((txn) => {
            const cat = (categoriesData ?? []).find(c => c.name === txn.category);
            const st  = statusConfig[txn.status] ?? statusConfig.selesai;
            return (
              <div key={txn.id}
                className="flex items-center gap-4 px-6 py-4 border-b border-slate-50 last:border-0 hover:bg-slate-50 transition-colors">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0"
                  style={{ backgroundColor: txn.type === 'income' ? '#D1FAE5' : txn.type === 'transfer' ? '#DBEAFE' : '#FEF2F2' }}>
                  {txn.type === 'income' ? '💰' : txn.type === 'transfer' ? '🔄' : (cat?.icon ?? '📦')}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-semibold text-slate-900 truncate">{txn.merchant}</p>
                    {/* ternary → badge status, hanya tampil kalau bukan 'selesai' */}
                    {txn.status && txn.status !== 'selesai' && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md shrink-0"
                        style={{ backgroundColor: st.bg, color: st.color }}>
                        {st.label}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{txn.category} · {txn.member} · {txn.account}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-bold" style={{ color: typeColors[txn.type] }}>
                    {txn.type === 'income' ? '+' : txn.type === 'transfer' ? '' : '-'}{formatRupiah(txn.amount)}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">{formatDate(txn.date)}</p>
                </div>
              </div>
            );
          })
        )}
      </Card>

      {/* Modal tambah transaksi */}
      {showForm && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4"
          style={{ backgroundColor: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)' }}>
          <div className="bg-white w-full max-w-md rounded-2xl p-6 max-h-[90vh] overflow-y-auto"
            style={{ boxShadow: 'rgba(0,0,0,0.25) 0px 32px 64px -12px' }}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-bold text-slate-900 text-lg">Tambah Transaksi Baru</h2>
              <button onClick={handleCloseForm} className="text-slate-400 hover:text-slate-700 text-xl">×</button>
            </div>

            {/* Warning duplikat */}
            {dupWarning && (
              <div className="mb-4 p-4 rounded-xl border border-amber-200 bg-amber-50">
                <p className="text-sm font-semibold text-amber-800 mb-1">⚠️ Kemungkinan Duplikat</p>
                <p className="text-xs text-amber-700">
                  Sudah ada transaksi <strong>{dupWarning.merchant}</strong> senilai{' '}
                  <strong>{formatRupiah(dupWarning.amount)}</strong> pada tanggal{' '}
                  <strong>{formatDate(dupWarning.date)}</strong>.
                </p>
                <div className="flex gap-2 mt-3">
                  <button type="button"
                    onClick={() => { setForceSave(true); setDupWarning(null); }}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-100 text-amber-800 hover:bg-amber-200 transition-colors">
                    Tetap Simpan
                  </button>
                  <button type="button"
                    onClick={() => setDupWarning(null)}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors">
                    Batalkan
                  </button>
                </div>
              </div>
            )}

            <form onSubmit={handleAdd} className="space-y-4">
              {/* Tipe */}
              <div className="flex gap-2">
                {['expense', 'income', 'transfer'].map((t) => (
                  <button type="button" key={t}
                    onClick={() => updateForm({ type: t })}
                    className="flex-1 py-2 rounded-xl text-xs font-semibold transition-all border"
                    style={{
                      backgroundColor: form.type === t ? typeColors[t] : 'transparent',
                      color: form.type === t ? '#fff' : '#64748B',
                      borderColor: form.type === t ? typeColors[t] : '#E2E8F0',
                    }}>
                    {typeLabels[t]}
                  </button>
                ))}
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Jumlah (Rp)</label>
                <input type="text" value={form.amount}
                  onChange={e => updateForm({ amount: e.target.value })}
                  placeholder="0" required
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-600 mb-1.5 block">Tanggal</label>
                  <input type="date" value={form.date}
                    onChange={e => updateForm({ date: e.target.value })}
                    className="w-full px-3 py-3 rounded-xl border border-slate-200 text-sm outline-none" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 mb-1.5 block">Anggota</label>
                  <select value={form.member} onChange={e => updateForm({ member: e.target.value })}
                    className="w-full px-3 py-3 rounded-xl border border-slate-200 text-sm outline-none bg-white">
                    {members.map(m => <option key={m}>{m}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Kategori</label>
                <select value={form.category || defaultCat} onChange={e => updateForm({ category: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none bg-white">
                  {categories.map(c => <option key={c.name} value={c.name}>{c.icon} {c.name}</option>)}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Merchant / Toko</label>
                <input type="text" value={form.merchant}
                  onChange={e => updateForm({ merchant: e.target.value })}
                  placeholder="cth: Indomaret, Grab, PLN..." required
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Rekening</label>
                <select value={form.account} onChange={e => updateForm({ account: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none bg-white">
                  {accounts.map(a => <option key={a}>{a}</option>)}
                </select>
              </div>

              {/* Status */}
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Status</label>
                <div className="flex gap-2">
                  {Object.entries(statusConfig).map(([key, cfg]) => (
                    <button type="button" key={key}
                      onClick={() => updateForm({ status: key })}
                      className="flex-1 py-2 rounded-xl text-xs font-semibold transition-all border"
                      style={{
                        backgroundColor: form.status === key ? cfg.bg : 'transparent',
                        color: form.status === key ? cfg.color : '#94A3B8',
                        borderColor: form.status === key ? cfg.bg : '#E2E8F0',
                      }}>
                      {cfg.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Catatan (opsional)</label>
                <textarea value={form.notes} onChange={e => updateForm({ notes: e.target.value })}
                  placeholder="Tambahkan catatan..." rows={2}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors resize-none" />
              </div>

              <div className="flex gap-3 pt-2">
                <Button variant="outline" fullWidth onClick={handleCloseForm}>Batal</Button>
                <Button type="submit" fullWidth disabled={submitting}>
                  {submitting ? 'Menyimpan...' : 'Simpan'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
