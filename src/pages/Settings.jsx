// Alur data: Settings → getCategories → localStorage → tampilan

import { useState } from 'react';
import { useFetch } from '../hooks/useFetch';
import { getCategories, postCategory, putCategory, getAccounts, postAccount, putAccount, deleteAccount } from '../API/getData';
import { track } from '../utils/analytics';
import { useToast } from '../context/ToastContext';
import { formatRupiah } from '../data/mockData';

const colorOptions = ['#F59E0B','#3B82F6','#EC4899','#8B5CF6','#10B981','#F97316','#06B6D4','#EF4444','#94A3B8','#0F172A'];
const iconOptions  = ['🍽️','🚗','🛍️','📚','💊','💡','🎬','📦','✈️','🏠','💰','🎁','🐾','💄','🏋️','📱','☕','🌿','🎮','💻'];

const accTypeOptions = [
  { value: 'bank',    label: 'Bank',    icon: '🏦' },
  { value: 'cash',    label: 'Tunai',   icon: '💵' },
  { value: 'ewallet', label: 'E-Wallet', icon: '📱' },
  { value: 'invest',  label: 'Investasi', icon: '📈' },
];

const accIconByType = { bank: '🏦', cash: '💵', ewallet: '📱', invest: '📈' };

const emptyAccForm = { name: '', icon: '🏦', type: 'bank', balance: '' };

// props → user dari App.jsx dipakai untuk baris profil di atas daftar anggota
export default function Settings({ user }) {
  const [householdName, setHouseholdName] = useState('Keluarga Budi Santoso');
  const [inviteEmail, setInviteEmail]     = useState('');
  const [saved, setSaved]                 = useState(false);

  // state form kategori baru
  const [showCatForm, setShowCatForm] = useState(false);
  const [catForm, setCatForm]         = useState({ name: '', icon: '📦', color: '#94A3B8' });
  const [catSaving, setCatSaving]     = useState(false);

  const { showToast } = useToast();
  const { data: categories, loading: loadCat, refetch: refetchCat } = useFetch(getCategories);

  // state rekening
  const [showAccForm, setShowAccForm]   = useState(false);
  const [accForm, setAccForm]           = useState(emptyAccForm);
  const [editingAcc, setEditingAcc]     = useState(null); // id akun yang sedang diedit
  const [accSaving, setAccSaving]       = useState(false);
  const [confirmDeleteAcc, setConfirmDeleteAcc] = useState(null);

  const { data: accList, loading: loadAcc, refetch: refetchAcc } = useFetch(getAccounts);

  const handleSave = () => {
    track('Settings:saveHousehold');
    setSaved(true);
    showToast('Informasi keluarga tersimpan');
    setTimeout(() => setSaved(false), 2000);
  };

  const handleAddCategory = async (e) => {
    e.preventDefault();
    if (!catForm.name.trim()) return;
    setCatSaving(true);
    track('Settings:addCategory', { name: catForm.name });
    await postCategory({ name: catForm.name.trim(), icon: catForm.icon, color: catForm.color, archived: false });
    refetchCat();
    showToast(`Kategori "${catForm.name.trim()}" berhasil ditambahkan`);
    setCatSaving(false);
    setShowCatForm(false);
    setCatForm({ name: '', icon: '📦', color: '#94A3B8' });
  };

  const handleToggleArchive = async (cat) => {
    track('Settings:toggleArchive', { name: cat.name, archived: !cat.archived });
    await putCategory(cat.name, { archived: !cat.archived });
    refetchCat();
    showToast(cat.archived ? `Kategori "${cat.name}" dipulihkan` : `Kategori "${cat.name}" diarsipkan`, 'info');
  };

  const cats        = categories ?? [];
  const activeCats  = cats.filter(c => !c.archived);
  const archivedCats = cats.filter(c => c.archived);

  const accs = accList ?? [];
  const totalBalance = accs.reduce((s, a) => s + (a.balance ?? 0), 0);

  const openAddAcc = () => {
    setEditingAcc(null);
    setAccForm(emptyAccForm);
    setShowAccForm(true);
  };

  const openEditAcc = (acc) => {
    setEditingAcc(acc.id);
    setAccForm({ name: acc.name, icon: acc.icon, type: acc.type, balance: String(acc.balance ?? '') });
    setShowAccForm(true);
  };

  const handleSaveAcc = async (e) => {
    e.preventDefault();
    if (!accForm.name.trim()) return;
    setAccSaving(true);
    const balanceNum = parseInt(accForm.balance.replace(/\D/g, ''), 10) || 0;
    if (editingAcc) {
      track('Settings:editAccount', { id: editingAcc });
      await putAccount(editingAcc, { name: accForm.name.trim(), icon: accForm.icon, type: accForm.type, balance: balanceNum });
      showToast(`Rekening "${accForm.name.trim()}" diperbarui`);
    } else {
      track('Settings:addAccount', { name: accForm.name });
      await postAccount({ id: String(Date.now()), name: accForm.name.trim(), icon: accForm.icon, type: accForm.type, balance: balanceNum });
      showToast(`Rekening "${accForm.name.trim()}" berhasil ditambahkan`);
    }
    refetchAcc();
    setAccSaving(false);
    setShowAccForm(false);
    setAccForm(emptyAccForm);
    setEditingAcc(null);
  };

  const handleDeleteAcc = async (id) => {
    track('Settings:deleteAccount', { id });
    await deleteAccount(id);
    refetchAcc();
    showToast('Rekening berhasil dihapus', 'info');
    setConfirmDeleteAcc(null);
  };

  // props user dipakai pada baris pertama, nilai bawaan dipakai bila props kosong
  const members = [
    { id: '1', name: user?.name ?? 'Budi Santoso', role: 'Ayah',
      email: user?.email ?? 'budi@gmail.com', avatar: user?.avatar ?? '👨' },
    { id: '2', name: 'Sari Santoso',  role: 'Ibu',  email: 'sari@gmail.com', avatar: '👩' },
    { id: '3', name: 'Dinda Santoso', role: 'Anak', email: '',               avatar: '🧒' },
  ];

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Konfigurasi</p>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Pengaturan</h1>
      </div>

      {/* Informasi keluarga */}
      <div className="bg-white rounded-2xl p-6" style={{ boxShadow: 'rgba(0,0,0,0.06) 0px 4px 20px -4px' }}>
        <h2 className="font-bold text-slate-900 mb-5 flex items-center gap-2">
          <span>🏠</span> Informasi Keluarga
        </h2>
        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-slate-600 mb-1.5 block">Nama Keluarga / Rumah Tangga</label>
            <input type="text" value={householdName}
              onChange={e => setHouseholdName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
          </div>
          <button onClick={handleSave}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-80 transition-all"
            style={{ backgroundColor: saved ? '#10B981' : '#0F172A' }}>
            {saved ? '✓ Tersimpan' : 'Simpan Perubahan'}
          </button>
        </div>
      </div>

      {/* Anggota keluarga */}
      <div className="bg-white rounded-2xl p-6" style={{ boxShadow: 'rgba(0,0,0,0.06) 0px 4px 20px -4px' }}>
        <h2 className="font-bold text-slate-900 mb-5 flex items-center gap-2">
          <span>👨‍👩‍👧</span> Anggota Keluarga
        </h2>
        <div className="space-y-3 mb-6">
          {members.map(m => (
            <div key={m.id} className="flex items-center gap-4 p-4 rounded-xl bg-slate-50">
              <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center text-xl shadow-sm shrink-0">
                {m.avatar}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-slate-900 text-sm">{m.name}</p>
                <p className="text-xs text-slate-400">{m.role}{m.email ? ` · ${m.email}` : ' · Tanpa akun'}</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-500 shrink-0">
                {m.role}
              </span>
            </div>
          ))}
        </div>
        <div>
          <label className="text-xs font-medium text-slate-600 mb-1.5 block">Undang Anggota via Email</label>
          <div className="flex gap-2">
            <input type="email" value={inviteEmail}
              onChange={e => setInviteEmail(e.target.value)}
              placeholder="email@contoh.com"
              className="flex-1 px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
            <button onClick={() => setInviteEmail('')}
              className="px-4 py-3 rounded-xl text-sm font-semibold text-white hover:opacity-80 transition-opacity shrink-0"
              style={{ backgroundColor: '#0F172A' }}>
              Undang
            </button>
          </div>
        </div>
      </div>

      {/* Kategori custom */}
      <div className="bg-white rounded-2xl p-6" style={{ boxShadow: 'rgba(0,0,0,0.06) 0px 4px 20px -4px' }}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-slate-900 flex items-center gap-2">
            <span>🏷️</span> Kategori Transaksi
          </h2>
          <button onClick={() => setShowCatForm(true)}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-white hover:opacity-80 transition-opacity"
            style={{ backgroundColor: '#0F172A' }}>
            + Kategori Baru
          </button>
        </div>

        {loadCat ? (
          <p className="text-sm text-slate-400 text-center py-4">Memuat...</p>
        ) : (
          <>
            <div className="space-y-2">
              {activeCats.map(cat => (
                <div key={cat.name} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base shrink-0"
                    style={{ backgroundColor: cat.color + '20' }}>
                    {cat.icon}
                  </div>
                  <span className="text-sm font-medium text-slate-800 flex-1">{cat.name}</span>
                  <button onClick={() => handleToggleArchive(cat)}
                    className="text-xs text-slate-400 hover:text-red-500 transition-colors px-2 py-1">
                    Arsipkan
                  </button>
                </div>
              ))}
            </div>

            {archivedCats.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Diarsipkan</p>
                <div className="space-y-2">
                  {archivedCats.map(cat => (
                    <div key={cat.name} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 opacity-50">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base shrink-0"
                        style={{ backgroundColor: cat.color + '20' }}>
                        {cat.icon}
                      </div>
                      <span className="text-sm font-medium text-slate-500 flex-1 line-through">{cat.name}</span>
                      <button onClick={() => handleToggleArchive(cat)}
                        className="text-xs text-slate-400 hover:text-emerald-500 transition-colors px-2 py-1">
                        Pulihkan
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Rekening & Dompet */}
      <div className="bg-white rounded-2xl p-6" style={{ boxShadow: 'rgba(0,0,0,0.06) 0px 4px 20px -4px' }}>
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-bold text-slate-900 flex items-center gap-2">
            <span>💳</span> Rekening & Dompet
          </h2>
          <button onClick={openAddAcc}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-white hover:opacity-80 transition-opacity"
            style={{ backgroundColor: '#0F172A' }}>
            + Tambah
          </button>
        </div>
        {/* Total saldo */}
        <p className="text-xs text-slate-400 mb-4">
          Total saldo: <span className="font-semibold text-slate-700">{formatRupiah(totalBalance)}</span>
        </p>

        {loadAcc ? (
          <p className="text-sm text-slate-400 text-center py-4">Memuat...</p>
        ) : (
          <div className="space-y-2">
            {accs.map(acc => (
              <div key={acc.id} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50">
                <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center text-lg shadow-sm shrink-0">
                  {acc.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-800">{acc.name}</p>
                  <p className="text-xs text-slate-400">{accTypeOptions.find(t => t.value === acc.type)?.label ?? acc.type}</p>
                </div>
                <p className="text-sm font-bold text-slate-700 shrink-0">{formatRupiah(acc.balance ?? 0)}</p>
                <div className="flex items-center gap-1 shrink-0 ml-1">
                  <button onClick={() => openEditAcc(acc)}
                    className="text-xs text-slate-400 hover:text-slate-700 transition-colors px-1.5 py-1">
                    Edit
                  </button>
                  <button onClick={() => setConfirmDeleteAcc(acc)}
                    className="text-xs text-slate-400 hover:text-red-500 transition-colors px-1.5 py-1">
                    Hapus
                  </button>
                </div>
              </div>
            ))}
            {accs.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-4">Belum ada rekening. Tambahkan satu.</p>
            )}
          </div>
        )}
      </div>

      {/* Danger zone */}
      <div className="bg-white rounded-2xl p-6 border border-red-100" style={{ boxShadow: 'rgba(0,0,0,0.06) 0px 4px 20px -4px' }}>
        <h2 className="font-bold text-red-600 mb-4 flex items-center gap-2">
          <span>⚠️</span> Zona Berbahaya
        </h2>
        <p className="text-sm text-slate-600 mb-4">
          Hapus semua data keluarga ini secara permanen. Tindakan ini tidak dapat dibatalkan.
        </p>
        <button className="px-5 py-2.5 rounded-xl border border-red-200 text-sm font-semibold text-red-600 hover:bg-red-50 transition-colors">
          Hapus Data Keluarga
        </button>
      </div>

      {/* Modal tambah/edit rekening */}
      {showAccForm && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4"
          style={{ backgroundColor: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)' }}>
          <div className="bg-white w-full max-w-sm rounded-2xl p-6"
            style={{ boxShadow: 'rgba(0,0,0,0.25) 0px 32px 64px -12px' }}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-bold text-slate-900">{editingAcc ? 'Edit Rekening' : 'Rekening Baru'}</h3>
              <button onClick={() => setShowAccForm(false)} className="text-slate-400 text-xl leading-none">×</button>
            </div>
            <form onSubmit={handleSaveAcc} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Nama Rekening</label>
                <input type="text" value={accForm.name}
                  onChange={e => setAccForm({ ...accForm, name: e.target.value })}
                  placeholder="cth: BCA Utama, Tunai Dompet" required autoFocus
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Tipe</label>
                <div className="grid grid-cols-2 gap-2">
                  {accTypeOptions.map(t => (
                    <button key={t.value} type="button"
                      onClick={() => setAccForm({ ...accForm, type: t.value, icon: accIconByType[t.value] })}
                      className="flex items-center gap-2 p-3 rounded-xl border text-left transition-all"
                      style={{
                        backgroundColor: accForm.type === t.value ? '#0F172A' : '#F8FAFC',
                        borderColor: accForm.type === t.value ? '#0F172A' : '#E2E8F0',
                        color: accForm.type === t.value ? '#fff' : '#475569',
                      }}>
                      <span>{t.icon}</span>
                      <span className="text-xs font-semibold">{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Saldo Awal (Rp)</label>
                <input type="text" value={accForm.balance}
                  onChange={e => setAccForm({ ...accForm, balance: e.target.value })}
                  placeholder="0"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
              </div>

              {/* Preview */}
              <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50">
                <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center text-lg shadow-sm">
                  {accForm.icon}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-slate-800">{accForm.name || 'Nama rekening...'}</p>
                  <p className="text-xs text-slate-400">{accTypeOptions.find(t => t.value === accForm.type)?.label}</p>
                </div>
                <p className="text-sm font-bold text-slate-700">
                  {formatRupiah(parseInt(accForm.balance.replace(/\D/g, ''), 10) || 0)}
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowAccForm(false)}
                  className="flex-1 py-3 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors">
                  Batal
                </button>
                <button type="submit" disabled={accSaving}
                  className="flex-1 py-3 rounded-xl text-sm font-semibold text-white hover:opacity-80 transition-all disabled:opacity-50"
                  style={{ backgroundColor: '#0F172A' }}>
                  {accSaving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Konfirmasi hapus rekening */}
      {confirmDeleteAcc && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4"
          style={{ backgroundColor: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)' }}>
          <div className="bg-white w-full max-w-xs rounded-2xl p-6 text-center"
            style={{ boxShadow: 'rgba(0,0,0,0.25) 0px 32px 64px -12px' }}>
            <div className="text-3xl mb-3">{confirmDeleteAcc.icon}</div>
            <h3 className="font-bold text-slate-900 mb-1">Hapus Rekening?</h3>
            <p className="text-sm text-slate-500 mb-5">
              <strong>{confirmDeleteAcc.name}</strong> akan dihapus permanen. Transaksi terkait tidak terpengaruh.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmDeleteAcc(null)}
                className="flex-1 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors">
                Batal
              </button>
              <button onClick={() => handleDeleteAcc(confirmDeleteAcc.id)}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white bg-red-500 hover:bg-red-600 transition-colors">
                Hapus
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal tambah kategori */}
      {showCatForm && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4"
          style={{ backgroundColor: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)' }}>
          <div className="bg-white w-full max-w-sm rounded-2xl p-6"
            style={{ boxShadow: 'rgba(0,0,0,0.25) 0px 32px 64px -12px' }}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-bold text-slate-900">Kategori Baru</h3>
              <button onClick={() => setShowCatForm(false)} className="text-slate-400 text-xl leading-none">×</button>
            </div>
            <form onSubmit={handleAddCategory} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Nama Kategori</label>
                <input type="text" value={catForm.name}
                  onChange={e => setCatForm({ ...catForm, name: e.target.value })}
                  placeholder="cth: Hobi, Perawatan" required autoFocus
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:border-slate-400 transition-colors" />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Ikon</label>
                <div className="flex flex-wrap gap-2">
                  {iconOptions.map(ico => (
                    <button key={ico} type="button"
                      onClick={() => setCatForm({ ...catForm, icon: ico })}
                      className="w-9 h-9 rounded-lg text-lg flex items-center justify-center transition-all"
                      style={{ backgroundColor: catForm.icon === ico ? '#0F172A' : '#F1F5F9' }}>
                      {ico}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 mb-1.5 block">Warna</label>
                <div className="flex flex-wrap gap-2">
                  {colorOptions.map(col => (
                    <button key={col} type="button"
                      onClick={() => setCatForm({ ...catForm, color: col })}
                      className="w-7 h-7 rounded-full border-2 transition-all"
                      style={{
                        backgroundColor: col,
                        borderColor: catForm.color === col ? '#0F172A' : 'transparent',
                        transform: catForm.color === col ? 'scale(1.2)' : 'scale(1)',
                      }} />
                  ))}
                </div>
              </div>

              {/* Preview */}
              <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg"
                  style={{ backgroundColor: catForm.color + '20' }}>
                  {catForm.icon}
                </div>
                <span className="text-sm font-medium text-slate-800">
                  {catForm.name || 'Nama kategori...'}
                </span>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCatForm(false)}
                  className="flex-1 py-3 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors">
                  Batal
                </button>
                <button type="submit" disabled={catSaving}
                  className="flex-1 py-3 rounded-xl text-sm font-semibold text-white hover:opacity-80 transition-all disabled:opacity-50"
                  style={{ backgroundColor: '#0F172A' }}>
                  {catSaving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
