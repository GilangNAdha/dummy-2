// Alur data: Goals (luar fetch) → getGoals → localStorage → tampilan

import { useState } from 'react';
import { useFetch } from '../hooks/useFetch';
import { getGoals, postGoalContribution } from '../API/getData';
import { save, load } from '../utils/localStorage';
import { track } from '../utils/analytics';
import { useToast } from '../context/ToastContext';
import { formatRupiah } from '../data/mockData';
import Card from '../components/Card';
import Button from '../components/Button';

const iconOptions = ['🎯', '✈️', '🏠', '🏍️', '🚗', '📱', '🛡️', '💍', '🎓', '🏥'];

export default function Goals() {
  const [showForm, setShowForm]     = useState(false);
  const [showContrib, setShowContrib] = useState(null);
  const [contribAmount, setContribAmount] = useState('');
  const [form, setForm] = useState({ name: '', target: '', deadline: '', icon: '🎯', color: '#3B82F6' });

  const { showToast } = useToast();
  const { data: goals, loading, error, refetch } = useFetch(getGoals);

  track('Goals:render');

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-slate-200 border-t-slate-800 rounded-full animate-spin" />
    </div>
  );

  if (error) return <Card><p className="text-red-500 text-sm">⚠️ {error}</p></Card>;

  const goalList = goals ?? [];
  const totalSaved  = goalList.reduce((s, g) => s + g.current, 0);
  const totalTarget = goalList.reduce((s, g) => s + g.target, 0);

  const addGoal = (e) => {
    e.preventDefault();
    const newGoal = {
      id: String(Date.now()),
      name: form.name,
      target: parseInt(form.target.replace(/\D/g, ''), 10) || 0,
      current: 0,
      deadline: form.deadline,
      icon: form.icon,
      color: form.color,
    };
    track('Goals:addGoal', { name: newGoal.name, target: newGoal.target });
    // spread operator → gabung goal baru dengan yang lama
    const updated = [newGoal, ...goalList];
    save('kf_goals', updated);
    refetch();
    showToast(`Tujuan "${newGoal.name}" berhasil dibuat`);
    setShowForm(false);
    setForm({ name: '', target: '', deadline: '', icon: '🎯', color: '#3B82F6' });
  };

  const addContrib = async (goalId) => {
    const amt = parseInt(contribAmount.replace(/\D/g, ''), 10) || 0;
    track('Goals:addContribution', { goalId, amount: amt });
    await postGoalContribution(goalId, amt);
    refetch();
    showToast(`Dana ${formatRupiah(amt)} berhasil ditambahkan`);
    setShowContrib(null);
    setContribAmount('');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Keuangan</p>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Tujuan Tabungan</h1>
        </div>
        <Button onClick={() => setShowForm(true)}>+ Tujuan Baru</Button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card padding="p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Total Terkumpul</p>
          <p className="text-2xl font-bold text-slate-900">{formatRupiah(totalSaved)}</p>
        </Card>
        <Card padding="p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Total Target</p>
          <p className="text-2xl font-bold text-slate-900">{formatRupiah(totalTarget)}</p>
        </Card>
      </div>

      {/* ternary → empty state */}
      {goalList.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-3xl mb-3">🎯</p>
          <p className="font-semibold text-slate-700 mb-1">Belum ada tujuan tabungan</p>
          <p className="text-sm text-slate-400">Tambah tujuan pertamamu sekarang.</p>
        </Card>
      ) : (
        // map → daftar goals
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {goalList.map((goal) => {
            const pct       = Math.round((goal.current / goal.target) * 100);
            const remaining = goal.target - goal.current;
            const deadline  = new Date(goal.deadline).toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' });
            // ternary → status selesai
            const done = pct >= 100;

            return (
              <Card key={goal.id} padding="p-5">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl"
                      style={{ backgroundColor: goal.color + '18' }}>
                      {goal.icon}
                    </div>
                    <div>
                      <p className="font-bold text-slate-900">{goal.name}</p>
                      <p className="text-xs text-slate-400 mt-0.5">Tenggat: {deadline}</p>
                    </div>
                  </div>
                  {/* ternary → badge tercapai */}
                  {done && <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600">✓ Tercapai</span>}
                </div>

                <div className="mb-3">
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="font-semibold text-slate-700">{formatRupiah(goal.current)}</span>
                    <span className="text-slate-400">{formatRupiah(goal.target)}</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all"
                      style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: goal.color }} />
                  </div>
                  <p className="text-xs text-slate-400 mt-1.5">
                    {/* ternary → teks status */}
                    {done ? 'Tujuan tercapai! 🎉' : `Sisa ${formatRupiah(remaining)} · ${pct}% terkumpul`}
                  </p>
                </div>

                {!done && (
                  <Button variant="outline" fullWidth className="text-xs !py-2" onClick={() => setShowContrib(goal.id)}>
                    + Tambah Dana
                  </Button>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Modal kontribusi */}
      {showContrib && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4"
          style={{ backgroundColor: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)' }}>
          <div className="bg-white w-full max-w-sm rounded-2xl p-6"
            style={{ boxShadow: 'rgba(0,0,0,0.25) 0px 32px 64px -12px' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-slate-900">Tambah Dana</h2>
              <button onClick={() => setShowContrib(null)} className="text-slate-400 text-xl">×</button>
            </div>
            <p className="text-sm text-slate-600 mb-4">{goalList.find(g => g.id === showContrib)?.name}</p>
            <input type="text" value={contribAmount} onChange={e => setContribAmount(e.target.value)}
              placeholder="Jumlah (Rp)"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors mb-4" />
            <div className="flex gap-3">
              <Button variant="outline" fullWidth onClick={() => setShowContrib(null)}>Batal</Button>
              <Button fullWidth onClick={() => addContrib(showContrib)}>Simpan</Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal tujuan baru */}
      {showForm && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4"
          style={{ backgroundColor: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)' }}>
          <div className="bg-white w-full max-w-sm rounded-2xl p-6"
            style={{ boxShadow: 'rgba(0,0,0,0.25) 0px 32px 64px -12px' }}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-bold text-slate-900">Tujuan Tabungan Baru</h2>
              <button onClick={() => setShowForm(false)} className="text-slate-400 text-xl">×</button>
            </div>
            <form onSubmit={addGoal} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Nama Tujuan</label>
                <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="cth: Liburan keluarga" required
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Target (Rp)</label>
                <input type="text" value={form.target} onChange={e => setForm({ ...form, target: e.target.value })}
                  placeholder="cth: 15000000" required
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Tenggat Waktu</label>
                <input type="date" value={form.deadline} onChange={e => setForm({ ...form, deadline: e.target.value })}
                  required className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Ikon</label>
                {/* map → pilihan ikon */}
                <div className="flex flex-wrap gap-2">
                  {iconOptions.map(ico => (
                    <button type="button" key={ico} onClick={() => setForm({ ...form, icon: ico })}
                      className="w-9 h-9 rounded-lg text-lg flex items-center justify-center transition-all"
                      style={{ backgroundColor: form.icon === ico ? '#0F172A' : '#F1F5F9' }}>
                      {ico}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <Button variant="outline" fullWidth onClick={() => setShowForm(false)}>Batal</Button>
                <Button type="submit" fullWidth>Buat Tujuan</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
