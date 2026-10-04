// Alur data: Dashboard (luar fetch) → getTransactions/getBudgets → localStorage → tampilan

import { useFetch } from '../hooks/useFetch';
import { getTransactions, getBudgets } from '../API/getData';
import { track } from '../utils/analytics';
import Card from '../components/Card';
import { formatRupiah, formatDate } from '../data/mockData';

const categoryIconMap = {
  'Makanan & Minuman': '🍽️', 'Transportasi': '🚗', 'Pendidikan': '📚',
  'Tagihan & Utilitas': '💡', 'Kesehatan': '💊', 'Belanja': '🛍️',
  'Hiburan': '🎬', 'Lainnya': '📦',
};

function StatCard({ label, amount, sub, color }) {
  return (
    <Card padding="p-6">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">{label}</p>
      <p className="text-2xl font-bold tracking-tight" style={{ color }}>
        {formatRupiah(Math.abs(amount))}
      </p>
      <p className="text-xs text-slate-400 mt-1">{sub}</p>
    </Card>
  );
}

// props → user dikirim dari App.jsx, dipakai untuk sapaan di kepala halaman
export default function Dashboard({ user }) {
  // useFetch → isi alur deps/refetch
  const { data: transactions, loading: loadTxn, error: errTxn } = useFetch(getTransactions);
  const { data: budgets, loading: loadBudget } = useFetch(getBudgets);

  track('Dashboard:render');

  // Loading state — ternary
  if (loadTxn || loadBudget) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-slate-200 border-t-slate-800 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Memuat data...</p>
        </div>
      </div>
    );
  }

  // Error state — ternary
  if (errTxn) {
    return (
      <Card>
        <p className="text-red-500 text-sm">⚠️ Gagal memuat data: {errTxn}</p>
      </Card>
    );
  }

  const txns = transactions ?? [];
  const bdgs = budgets ?? [];

  // transaksi dibatalkan tidak dihitung
  const activeTxns = txns.filter(t => t.status !== 'dibatalkan');

  const totalIncome  = activeTxns.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0);
  const totalExpense = activeTxns.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0);
  const netFlow      = totalIncome - totalExpense;

  // hitung spent per kategori dari transaksi nyata
  const spentMap = {};
  activeTxns.filter(t => t.type === 'expense').forEach(t => {
    spentMap[t.category] = (spentMap[t.category] ?? 0) + t.amount;
  });

  // map → kategori teratas
  const categoryTotals = bdgs
    .map(b => ({ ...b, spent: spentMap[b.category] ?? 0 }))
    .map(b => ({ ...b, pct: b.limit > 0 ? Math.round((b.spent / b.limit) * 100) : 0 }))
    .sort((a, b) => b.spent - a.spent)
    .slice(0, 4);

  // map → transaksi terbaru
  const recentTxns = [...txns]
    .filter(t => t.type !== 'transfer')
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 6);

  // notifikasi anggaran: lewat (>=100%) atau mendekati (>=80%)
  const budgetAlerts = bdgs
    .map(b => ({ ...b, spent: spentMap[b.category] ?? 0 }))
    .map(b => ({ ...b, pct: b.limit > 0 ? Math.round((b.spent / b.limit) * 100) : 0 }))
    .filter(b => b.pct >= 80)
    .sort((a, b) => b.pct - a.pct);

  const now = new Date();
  const bulanIni = now.toLocaleDateString('id-ID', { month: 'long', year: 'numeric' });

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">{bulanIni}</p>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Ringkasan Bulan Ini</h1>
        <p className="text-xs text-slate-400 mt-1">
          Halo, {user?.name ?? 'Budi Santoso'}{user?.household ? ` dari ${user.household}` : ''}
        </p>
      </div>

      {/* Notifikasi anggaran — ternary + map */}
      {budgetAlerts.length > 0 && (
        <div className="space-y-2">
          {budgetAlerts.map(b => {
            const isOver = b.pct >= 100;
            return (
              <div key={b.category}
                className="flex items-center gap-3 px-4 py-3 rounded-xl border"
                style={{
                  backgroundColor: isOver ? '#FEF2F2' : '#FFFBEB',
                  borderColor:     isOver ? '#FECACA' : '#FDE68A',
                }}>
                <span className="text-lg shrink-0">{isOver ? '🚨' : '⚠️'}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold" style={{ color: isOver ? '#991B1B' : '#92400E' }}>
                    {isOver ? 'Anggaran terlampaui' : 'Anggaran hampir habis'} — {b.category}
                  </p>
                  <p className="text-xs mt-0.5" style={{ color: isOver ? '#B91C1C' : '#B45309' }}>
                    {formatRupiah(b.spent)} dari {formatRupiah(b.limit)} ({b.pct}%)
                  </p>
                </div>
                <span className="text-xs font-bold px-2 py-1 rounded-lg shrink-0"
                  style={{
                    backgroundColor: isOver ? '#FEE2E2' : '#FEF3C7',
                    color:           isOver ? '#991B1B' : '#92400E',
                  }}>
                  {b.pct}%
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* StatCards — props */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total Pemasukan" amount={totalIncome}  sub="Bulan Januari" color="#10B981" />
        <StatCard label="Total Pengeluaran" amount={totalExpense} sub="Bulan Januari" color="#EF4444" />
        <StatCard
          label="Arus Kas Bersih"
          amount={netFlow}
          sub={netFlow >= 0 ? 'Surplus bulan ini' : 'Defisit bulan ini'}
          color={netFlow >= 0 ? '#0F172A' : '#EF4444'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Kategori teratas — map */}
        <Card className="lg:col-span-2">
          <h2 className="font-bold text-slate-900 mb-5">Kategori Teratas</h2>
          {categoryTotals.length === 0 ? (
            // ternary → empty state
            <p className="text-sm text-slate-400">Belum ada data anggaran.</p>
          ) : (
            <div className="space-y-4">
              {categoryTotals.map((cat) => (
                <div key={cat.category}>
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-base">{cat.icon}</span>
                      <span className="text-sm font-medium text-slate-700 truncate max-w-[120px]">{cat.category}</span>
                    </div>
                    <span className="text-sm font-semibold text-slate-900">{formatRupiah(cat.spent)}</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.min(cat.pct, 100)}%`,
                        // ternary → warna bar berdasarkan status
                        backgroundColor: cat.pct >= 90 ? '#EF4444' : cat.pct >= 75 ? '#F59E0B' : cat.color,
                      }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{cat.pct}% dari {formatRupiah(cat.limit)}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Transaksi terbaru — map */}
        <Card className="lg:col-span-3">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-bold text-slate-900">Transaksi Terbaru</h2>
          </div>
          {/* ternary → empty state */}
          {recentTxns.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">Belum ada transaksi.</p>
          ) : (
            <div className="space-y-3">
              {recentTxns.map((txn) => (
                <div key={txn.id} className="flex items-center gap-3 py-2 border-b border-slate-50 last:border-0">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-base shrink-0"
                    style={{ backgroundColor: txn.type === 'income' ? '#D1FAE5' : '#FEF2F2' }}
                  >
                    {txn.type === 'income' ? '💰' : (categoryIconMap[txn.category] ?? '📦')}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">{txn.merchant}</p>
                    <p className="text-xs text-slate-400">{txn.member} · {formatDate(txn.date)}</p>
                  </div>
                  <p className="text-sm font-semibold shrink-0" style={{ color: txn.type === 'income' ? '#10B981' : '#EF4444' }}>
                    {txn.type === 'income' ? '+' : '-'}{formatRupiah(txn.amount)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Pengeluaran per anggota — map */}
      <Card>
        <h2 className="font-bold text-slate-900 mb-5">Pengeluaran per Anggota</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            { name: 'Ayah', avatar: '👨', color: '#3B82F6' },
            { name: 'Ibu',  avatar: '👩', color: '#EC4899' },
            { name: 'Anak', avatar: '🧒', color: '#8B5CF6' },
          ].map(({ name, avatar, color }) => {
            const spent = txns
              .filter(t => t.member === name && t.type === 'expense' && t.status !== 'dibatalkan')
              .reduce((s, t) => s + t.amount, 0);
            return (
              <div key={name} className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl bg-slate-50 shrink-0">{avatar}</div>
                <div>
                  <p className="font-semibold text-slate-900">{name}</p>
                  <p className="text-sm font-bold" style={{ color }}>{formatRupiah(spent)}</p>
                  <p className="text-xs text-slate-400">Pengeluaran bulan ini</p>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
