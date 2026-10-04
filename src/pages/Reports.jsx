// Alur data: Reports (luar fetch) → getTransactions → localStorage → tampilan

import { useState } from 'react';
import { useFetch } from '../hooks/useFetch';
import { getTransactions } from '../API/getData';
import { track } from '../utils/analytics';
import { formatRupiah, categories as allCategories } from '../data/mockData';
import Card from '../components/Card';

// lookup icon & color dari categories mockData
const categoryMeta = Object.fromEntries(
  allCategories.map(c => [c.name, { icon: c.icon, color: c.color }])
);

const months = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];

// Komponen bar chart tren bulanan
function Bar({ label, income, expense, maxVal, isCurrentMonth }) {
  const incPct = maxVal > 0 ? (income / maxVal) * 100 : 0;
  const expPct = maxVal > 0 ? (expense / maxVal) * 100 : 0;
  return (
    <div className="flex flex-col items-center gap-2 min-w-[44px]">
      <div className="flex items-end gap-1 h-32">
        <div className="w-4 rounded-t-md transition-all"
          style={{ height: `${incPct}%`, backgroundColor: isCurrentMonth ? '#10B981' : '#A7F3D0' }} />
        <div className="w-4 rounded-t-md transition-all"
          style={{ height: `${expPct}%`, backgroundColor: isCurrentMonth ? '#EF4444' : '#FECACA' }} />
      </div>
      <span className={`text-xs font-medium ${isCurrentMonth ? 'text-slate-800' : 'text-slate-400'}`}>{label}</span>
    </div>
  );
}

export default function Reports() {
  const [period, setPeriod] = useState('all');

  const { data: transactions, loading, error } = useFetch(getTransactions);

  track('Reports:render');

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-slate-200 border-t-slate-800 rounded-full animate-spin" />
    </div>
  );

  if (error) return <Card><p className="text-red-500 text-sm">⚠️ {error}</p></Card>;

  const allTxns = transactions ?? [];

  // filter transaksi sesuai period yang dipilih
  const txns = period === 'all'
    ? allTxns
    : allTxns.filter(t => t.date.startsWith(period));

  // transaksi dibatalkan tidak dihitung dalam kalkulasi apapun
  const activeTxns = txns.filter(t => t.status !== 'dibatalkan');

  // ── KPI ────────────────────────────────────────────────────
  const totalIncome  = activeTxns.filter(t => t.type === 'income').reduce((s, t)  => s + t.amount, 0);
  const totalExpense = activeTxns.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0);
  const totalSaving  = totalIncome - totalExpense;
  const savingsRate  = totalIncome > 0 ? Math.round((totalSaving / totalIncome) * 100) : 0;

  // ── Komposisi per kategori ──────────────────────────────────
  const categoryMap = {};
  activeTxns.filter(t => t.type === 'expense').forEach(t => {
    if (!categoryMap[t.category]) categoryMap[t.category] = 0;
    categoryMap[t.category] += t.amount;
  });
  const byCategory = Object.entries(categoryMap)
    .map(([category, spent]) => ({ category, spent, pct: totalExpense > 0 ? Math.round((spent / totalExpense) * 100) : 0 }))
    .sort((a, b) => b.spent - a.spent);

  // ── Grafik tren — build dari data transaksi nyata per bulan ─
  const monthlyMap = {};
  allTxns.forEach(t => {
    const m = t.date.slice(0, 7);
    if (!monthlyMap[m]) monthlyMap[m] = { income: 0, expense: 0 };
    if (t.status === 'dibatalkan') return;
    if (t.type === 'income')  monthlyMap[m].income  += t.amount;
    if (t.type === 'expense') monthlyMap[m].expense += t.amount;
  });
  const sortedMonths = Object.keys(monthlyMap).sort().slice(-6);
  const chartData = sortedMonths.map((m, i) => {
    const [y, mo] = m.split('-');
    return {
      label: months[parseInt(mo) - 1].slice(0, 3),
      income:  monthlyMap[m].income,
      expense: monthlyMap[m].expense,
      isCurrent: i === sortedMonths.length - 1,
    };
  });
  const maxVal = Math.max(...chartData.map(d => Math.max(d.income, d.expense)));

  // ── Ekspor CSV ─────────────────────────────────────────────
  const handleExportCSV = () => {
    track('Reports:exportCSV', { period, count: txns.length });
    const header = 'Tanggal,Jenis,Jumlah,Kategori,Anggota,Merchant,Catatan,Rekening\n';
    const rows = txns.map(t =>
      `${t.date},${t.type},${t.amount},${t.category},${t.member},${t.merchant},"${t.notes ?? ''}",${t.account}`
    ).join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `keluargafin_${period}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Analisis</p>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Laporan Keuangan</h1>
        </div>
        <button onClick={handleExportCSV}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors">
          <span>📤</span> Ekspor CSV
        </button>
      </div>

      {/* Period selector — generate dari transaksi yang ada */}
      {(() => {
        const uniqueMonths = [...new Set(allTxns.map(t => t.date.slice(0, 7)))].sort().reverse();
        return (
          <select value={period} onChange={e => setPeriod(e.target.value)}
            className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm text-slate-700 bg-white outline-none">
            <option value="all">Semua Periode</option>
            {uniqueMonths.map(p => {
              const [y, m] = p.split('-');
              return <option key={p} value={p}>{months[parseInt(m) - 1]} {y}</option>;
            })}
          </select>
        );
      })()}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Pemasukan',   value: formatRupiah(totalIncome),  color: '#10B981' },
          { label: 'Pengeluaran', value: formatRupiah(totalExpense), color: '#EF4444' },
          { label: 'Tabungan',    value: formatRupiah(totalSaving),  color: '#3B82F6' },
          { label: 'Rasio Hemat', value: `${savingsRate}%`,          color: savingsRate >= 20 ? '#10B981' : '#F59E0B' },
        ].map(k => (
          <Card key={k.label} padding="p-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">{k.label}</p>
            <p className="text-xl font-bold tracking-tight" style={{ color: k.color }}>{k.value}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar chart tren */}
        <Card padding="p-6">
          <h2 className="font-bold text-slate-900 mb-2">Tren 6 Bulan Terakhir</h2>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-emerald-400 inline-block" />
              <span className="text-xs text-slate-500">Pemasukan</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-red-400 inline-block" />
              <span className="text-xs text-slate-500">Pengeluaran</span>
            </div>
          </div>
          <div className="flex items-end gap-4 pb-2 overflow-x-auto">
            {chartData.map((d) => (
              <Bar key={d.label} label={d.label} income={d.income} expense={d.expense} maxVal={maxVal} isCurrentMonth={d.isCurrent} />
            ))}
          </div>
        </Card>

        {/* Komposisi kategori — dari transaksi nyata */}
        <Card padding="p-6">
          <h2 className="font-bold text-slate-900 mb-5">Komposisi Pengeluaran</h2>
          {byCategory.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-8">Belum ada transaksi pengeluaran.</p>
          ) : (
            <div className="space-y-4">
              {byCategory.slice(0, 6).map(cat => {
                const meta = categoryMeta[cat.category] ?? { icon: '📦', color: '#94A3B8' };
                return (
                  <div key={cat.category}>
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-base">{meta.icon}</span>
                        <span className="text-sm font-medium text-slate-700">{cat.category}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-slate-400">{cat.pct}%</span>
                        <span className="text-sm font-semibold text-slate-900">{formatRupiah(cat.spent)}</span>
                      </div>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all"
                        style={{ width: `${cat.pct}%`, backgroundColor: meta.color }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      {/* Tabel per anggota — dari transaksi nyata */}
      <Card padding="p-6">
        <h2 className="font-bold text-slate-900 mb-5">Ringkasan per Anggota</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                {['Anggota','Pemasukan','Pengeluaran','Transaksi'].map((h, i) => (
                  <th key={h} className={`text-xs font-semibold uppercase tracking-wider text-slate-400 pb-3 ${i === 0 ? 'text-left' : 'text-right'}`}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {[
                { name: 'Ayah', avatar: '👨' },
                { name: 'Ibu',  avatar: '👩' },
                { name: 'Anak', avatar: '🧒' },
              ].map(({ name, avatar }) => {
                const inc   = txns.filter(t => t.member === name && t.type === 'income').reduce((s, t)  => s + t.amount, 0);
                const exp   = activeTxns.filter(t => t.member === name && t.type === 'expense').reduce((s, t) => s + t.amount, 0);
                const count = txns.filter(t => t.member === name).length;
                return (
                  <tr key={name}>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{avatar}</span>
                        <span className="font-medium text-slate-900">{name}</span>
                      </div>
                    </td>
                    <td className="py-3 text-right font-semibold text-emerald-600">{inc > 0 ? formatRupiah(inc) : '—'}</td>
                    <td className="py-3 text-right font-semibold text-red-500">{exp > 0 ? formatRupiah(exp) : '—'}</td>
                    <td className="py-3 text-right text-slate-500">{count}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
