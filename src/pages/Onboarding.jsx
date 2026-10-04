// Onboarding flow: household → anggota → budget → goal → dashboard
// Data disimpan ke localStorage, siap diganti API nanti

import { useState } from 'react';
import { save } from '../utils/localStorage';
import { track } from '../utils/analytics';
import { categories, budgets as defaultBudgets } from '../data/mockData';

const STEPS = ['Household', 'Anggota', 'Budget', 'Tujuan'];

const memberTemplates = [
  { role: 'Ayah', avatar: '👨', placeholder: 'cth: Budi Santoso' },
  { role: 'Ibu',  avatar: '👩', placeholder: 'cth: Sari Santoso' },
  { role: 'Anak', avatar: '🧒', placeholder: 'cth: Dinda (opsional)' },
];

export default function Onboarding({ onDone }) {
  const [step, setStep] = useState(0);

  // Step 0 — household
  const [household, setHousehold] = useState('');

  // Step 1 — anggota
  const [members, setMembers] = useState([
    { role: 'Ayah', avatar: '👨', name: '' },
    { role: 'Ibu',  avatar: '👩', name: '' },
    { role: 'Anak', avatar: '🧒', name: '' },
  ]);

  // Step 2 — budget awal
  const [budgets, setBudgets] = useState(
    defaultBudgets.map(b => ({ ...b, limit: b.limit, active: true }))
  );

  // Step 3 — goal pertama (opsional)
  const [goal, setGoal] = useState({ name: '', target: '', deadline: '', icon: '🎯' });
  const [skipGoal, setSkipGoal] = useState(false);

  const iconOptions = ['🎯', '✈️', '🏠', '🏍️', '🚗', '📱', '🛡️', '💍', '🎓', '🏥'];

  // ── Validasi per step ──────────────────────────────────────
  const canNext = () => {
    if (step === 0) return household.trim().length >= 2;
    if (step === 1) return members[0].name.trim() || members[1].name.trim();
    if (step === 2) return budgets.some(b => b.active && b.limit > 0);
    return true;
  };

  // ── Simpan semua ke localStorage lalu masuk app ────────────
  const finish = () => {
    track('Onboarding:complete', { household, memberCount: members.filter(m => m.name).length });

    save('kf_household', { name: household, currency: 'IDR' });
    save('kf_members', members.filter(m => m.name.trim()));

    const activeBudgets = budgets
      .filter(b => b.active && b.limit > 0)
      .map(b => ({ ...b, spent: 0 }));
    save('kf_budgets', activeBudgets);

    if (!skipGoal && goal.name && goal.target) {
      save('kf_goals', [{
        id: String(Date.now()),
        name: goal.name,
        target: parseInt(goal.target.replace(/\D/g, ''), 10) || 0,
        current: 0,
        deadline: goal.deadline,
        icon: goal.icon,
        color: '#3B82F6',
      }]);
    }

    save('kf_onboarded', true);
    onDone({ name: members[0].name || household, household });
  };

  const next = () => {
    track('Onboarding:next', { step });
    if (step < STEPS.length - 1) setStep(s => s + 1);
    else finish();
  };

  const back = () => setStep(s => s - 1);

  // ── Render step ────────────────────────────────────────────
  const renderStep = () => {
    if (step === 0) return (
      <div className="space-y-5">
        <div className="text-center mb-6">
          <div className="text-5xl mb-4">🏠</div>
          <h2 className="text-xl font-bold text-slate-900">Buat Household</h2>
          <p className="text-sm text-slate-500 mt-1">Nama yang akan dipakai semua anggota keluarga</p>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600 mb-1.5 block">Nama Keluarga</label>
          <input
            type="text"
            value={household}
            onChange={e => setHousehold(e.target.value)}
            placeholder="cth: Keluarga Santoso"
            autoFocus
            className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors"
          />
          <p className="text-xs text-slate-400 mt-2">Minimal 2 karakter. Bisa diubah nanti di Pengaturan.</p>
        </div>
        <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
          <p className="text-xs text-blue-700 font-medium">🔒 Kami tidak meminta password atau PIN bank. Bukti transaksi hanya untuk membuat draft yang kamu review sendiri.</p>
        </div>
      </div>
    );

    if (step === 1) return (
      <div className="space-y-4">
        <div className="text-center mb-6">
          <div className="text-5xl mb-4">👨‍👩‍👧</div>
          <h2 className="text-xl font-bold text-slate-900">Profil Anggota</h2>
          <p className="text-sm text-slate-500 mt-1">Tambahkan nama anggota keluarga (minimal 1)</p>
        </div>
        {memberTemplates.map((tmpl, i) => (
          <div key={tmpl.role} className="flex items-center gap-3 p-4 rounded-xl bg-slate-50">
            <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center text-xl shadow-sm shrink-0">
              {tmpl.avatar}
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold text-slate-500 mb-1">{tmpl.role}</p>
              <input
                type="text"
                value={members[i].name}
                onChange={e => {
                  const updated = [...members];
                  updated[i] = { ...updated[i], name: e.target.value };
                  setMembers(updated);
                }}
                placeholder={tmpl.placeholder}
                className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-300"
              />
            </div>
          </div>
        ))}
      </div>
    );

    if (step === 2) return (
      <div className="space-y-3">
        <div className="text-center mb-6">
          <div className="text-5xl mb-4">📋</div>
          <h2 className="text-xl font-bold text-slate-900">Budget Awal</h2>
          <p className="text-sm text-slate-500 mt-1">Set batas pengeluaran per kategori bulan ini</p>
        </div>
        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          {budgets.map((b, i) => (
            <div key={b.category}
              className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${b.active ? 'bg-white border-slate-200' : 'bg-slate-50 border-slate-100 opacity-50'}`}>
              <button
                type="button"
                onClick={() => {
                  const updated = [...budgets];
                  updated[i] = { ...updated[i], active: !updated[i].active };
                  setBudgets(updated);
                }}
                className="w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all"
                style={{ borderColor: b.active ? b.color : '#CBD5E1', backgroundColor: b.active ? b.color : 'transparent' }}
              >
                {b.active && <span className="text-white text-xs">✓</span>}
              </button>
              <span className="text-lg">{b.icon}</span>
              <span className="text-sm font-medium text-slate-700 flex-1">{b.category}</span>
              <input
                type="number"
                value={b.limit}
                disabled={!b.active}
                onChange={e => {
                  const updated = [...budgets];
                  updated[i] = { ...updated[i], limit: parseInt(e.target.value) || 0 };
                  setBudgets(updated);
                }}
                className="w-28 text-right text-sm px-2 py-1 rounded-lg border border-slate-200 outline-none focus:border-slate-400 disabled:opacity-40"
                placeholder="0"
              />
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 text-center">Centang kategori yang ingin dianggarkan. Bisa diubah nanti.</p>
      </div>
    );

    if (step === 3) return (
      <div className="space-y-4">
        <div className="text-center mb-6">
          <div className="text-5xl mb-4">🎯</div>
          <h2 className="text-xl font-bold text-slate-900">Tujuan Tabungan</h2>
          <p className="text-sm text-slate-500 mt-1">Buat satu target keuangan pertama (opsional)</p>
        </div>

        {/* ternary → skip state */}
        {skipGoal ? (
          <div className="text-center py-6">
            <p className="text-slate-500 text-sm">Kamu bisa tambahkan tujuan tabungan kapan saja dari menu Tujuan.</p>
            <button onClick={() => setSkipGoal(false)} className="text-blue-500 text-sm mt-3 underline">
              Batal, isi sekarang
            </button>
          </div>
        ) : (
          <>
            <div>
              <label className="text-xs font-medium text-slate-600 mb-1.5 block">Nama Tujuan</label>
              <input type="text" value={goal.name}
                onChange={e => setGoal({ ...goal, name: e.target.value })}
                placeholder="cth: Dana Darurat, Liburan Keluarga"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 mb-1.5 block">Target (Rp)</label>
              <input type="number" value={goal.target}
                onChange={e => setGoal({ ...goal, target: e.target.value })}
                placeholder="cth: 10000000"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 mb-1.5 block">Tenggat Waktu</label>
              <input type="date" value={goal.deadline}
                onChange={e => setGoal({ ...goal, deadline: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 mb-1.5 block">Ikon</label>
              <div className="flex flex-wrap gap-2">
                {iconOptions.map(ico => (
                  <button key={ico} type="button" onClick={() => setGoal({ ...goal, icon: ico })}
                    className="w-9 h-9 rounded-lg text-lg flex items-center justify-center transition-all"
                    style={{ backgroundColor: goal.icon === ico ? '#0F172A' : '#F1F5F9' }}>
                    {ico}
                  </button>
                ))}
              </div>
            </div>
            <button onClick={() => setSkipGoal(true)}
              className="w-full text-center text-sm text-slate-400 hover:text-slate-600 transition-colors py-1">
              Lewati, atur nanti →
            </button>
          </>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#F8FAFC' }}>
      <div className="w-full max-w-md">
        {/* Header logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <span className="text-2xl">💰</span>
          <span className="font-bold text-slate-900 text-lg">KeluargaFin</span>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-2 mb-8">
          {STEPS.map((s, i) => (
            <div key={s} className="flex-1 flex flex-col items-center gap-1">
              <div className="w-full h-1.5 rounded-full transition-all"
                style={{ backgroundColor: i <= step ? '#0F172A' : '#E2E8F0' }} />
              <span className={`text-[10px] font-medium transition-colors ${i === step ? 'text-slate-800' : 'text-slate-300'}`}>
                {s}
              </span>
            </div>
          ))}
        </div>

        {/* Card konten */}
        <div className="bg-white rounded-3xl p-6 mb-4" style={{ boxShadow: 'rgba(0,0,0,0.08) 0px 8px 32px -8px' }}>
          {renderStep()}
        </div>

        {/* Tombol navigasi */}
        <div className="flex gap-3">
          {step > 0 && (
            <button onClick={back}
              className="flex-1 py-3 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors">
              ← Kembali
            </button>
          )}
          <button
            onClick={next}
            disabled={!canNext()}
            className="flex-1 py-3 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-40"
            style={{ backgroundColor: '#0F172A' }}
          >
            {step === STEPS.length - 1
              ? (skipGoal ? 'Masuk Dashboard →' : '🎉 Mulai Pakai!')
              : 'Lanjut →'}
          </button>
        </div>

        <p className="text-center text-xs text-slate-400 mt-4">
          Langkah {step + 1} dari {STEPS.length}
        </p>
      </div>
    </div>
  );
}
