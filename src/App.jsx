// App.jsx → shell utama, kirim props ke semua halaman

import { useState } from 'react';
import { ToastProvider } from './context/ToastContext';
import QuickAdd from './components/QuickAdd';
import { track } from './utils/analytics';
import { load } from './utils/localStorage';
import QAPanel from './components/QAPanel';
import AuthPage from './pages/AuthPage';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Budget from './pages/Budget';
import Goals from './pages/Goals';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

// props → navItems dikirim ke sidebar (semua halaman)
const navItems = [
  { id: 'dashboard',    label: 'Dashboard',   icon: '📊' },
  { id: 'transactions', label: 'Transaksi',    icon: '💸' },
  { id: 'budget',       label: 'Anggaran',     icon: '📋' },
  { id: 'goals',        label: 'Tujuan',       icon: '🎯' },
  { id: 'reports',      label: 'Laporan',      icon: '📈' },
  { id: 'settings',     label: 'Pengaturan',   icon: '⚙️' },
];

// bottom nav mobile: 2 kiri | FAB + | 2 kanan (tanpa Settings)
const bottomNavLeft  = [navItems[0], navItems[1]]; // Dashboard, Transaksi
const bottomNavRight = [navItems[2], navItems[3]]; // Anggaran, Tujuan

// props → user dikirim ke halaman yang butuh info user
const defaultUser = {
  name: 'Budi Santoso',
  email: 'budi@gmail.com',
  household: 'Keluarga Santoso',
  avatar: '👨',
};

const pages = {
  dashboard:    Dashboard,
  transactions: Transactions,
  budget:       Budget,
  goals:        Goals,
  reports:      Reports,
  settings:     Settings,
};

export default function App() {
  const [authed, setAuthed]             = useState(false);
  const [onboarded, setOnboarded]       = useState(() => !!load('kf_onboarded', false));
  const [page, setPage]                 = useState('dashboard');
  const [sidebarOpen, setSidebarOpen]   = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [user, setUser]                 = useState(defaultUser); // props → dikirim ke halaman

  const handleLogin = () => {
    track('App:login');
    setAuthed(true);
  };

  const handleLogout = () => {
    track('App:logout');
    // window.location.assign → redirect ke halaman awal
    window.location.assign('/');
  };

  const handleNavigate = (id) => {
    track('App:navigate', { to: id });
    setPage(id);
    setSidebarOpen(false);
  };

  // ternary → tampilkan AuthPage jika belum login
  if (!authed) return <AuthPage onLogin={handleLogin} />;

  // ternary → tampilkan Onboarding jika belum setup household
  if (!onboarded) return (
    <Onboarding onDone={({ name, household }) => {
      track('Onboarding:done', { household });
      setUser(u => ({ ...u, name, household }));
      setOnboarded(true);
    }} />
  );

  const PageComponent = pages[page];

  return (
    <ToastProvider>
    <div className="min-h-screen flex" style={{ backgroundColor: '#F8FAFC' }}>
      {/* Overlay mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          style={{ backgroundColor: 'rgba(15,23,42,0.4)', backdropFilter: 'blur(2px)' }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full z-50 flex flex-col transition-transform duration-300 ease-out lg:translate-x-0 lg:static lg:z-auto ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
        style={{ width: '240px', backgroundColor: '#0F172A' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-6 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-base">💰</div>
          <div>
            <p className="text-white font-bold text-base leading-tight">KeluargaFin</p>
            {/* props → nama household dari state user */}
            <p className="text-white/40 text-xs">{user.household}</p>
          </div>
        </div>

        {/* Nav — map navItems */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavigate(item.id)}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-left"
              style={{
                // ternary → highlight halaman aktif
                backgroundColor: page === item.id ? 'rgba(255,255,255,0.12)' : 'transparent',
                color:           page === item.id ? '#fff' : 'rgba(255,255,255,0.5)',
              }}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        {/* User info — props user */}
        <div className="px-4 py-4 border-t border-white/10">
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-sm">
              {user.avatar}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-xs font-semibold truncate">{user.name}</p>
              <p className="text-white/40 text-xs truncate">{user.email}</p>
            </div>
            <button onClick={handleLogout} title="Keluar"
              className="text-white/30 hover:text-white/70 transition-colors text-sm">
              ⎋
            </button>
          </div>
        </div>
      </aside>

      {/* Konten utama */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header mobile */}
        <header className="lg:hidden flex items-center justify-between px-4 py-4 bg-white border-b border-slate-100 sticky top-0 z-30"
          style={{ boxShadow: 'rgba(0,0,0,0.04) 0px 1px 8px' }}>
          <button onClick={() => setSidebarOpen(true)}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-slate-100 text-slate-600">
            ☰
          </button>
          <div className="flex items-center gap-2">
            <span className="text-base">💰</span>
            <span className="font-bold text-slate-900 text-sm">KeluargaFin</span>
          </div>
          <div className="w-9 h-9" />
        </header>

        {/* Halaman — props user dikirim ke PageComponent */}
        <main className="flex-1 p-6 lg:p-8 overflow-auto">
          <PageComponent user={user} />
        </main>

        {/* Bottom nav: Dashboard | Transaksi | [+] | Anggaran | Laporan */}
        <nav className="lg:hidden flex items-center border-t border-slate-100 bg-white sticky bottom-0 z-30">
          {bottomNavLeft.map((item) => (
            <button key={item.id} onClick={() => handleNavigate(item.id)}
              className="flex-1 flex flex-col items-center gap-0.5 py-3 transition-colors"
              style={{ color: page === item.id ? '#0F172A' : '#94A3B8' }}>
              <span className="text-lg leading-none">{item.icon}</span>
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          ))}
          <div className="flex-1 flex justify-center">
            <button
              onClick={() => { track('App:quickAdd'); setQuickAddOpen(true); }}
              className="w-14 h-14 rounded-full flex items-center justify-center text-white text-2xl font-light -mt-5 transition-transform active:scale-95"
              style={{ backgroundColor: '#0F172A', boxShadow: 'rgba(15,23,42,0.35) 0px 8px 24px -4px' }}>
              +
            </button>
          </div>
          {bottomNavRight.map((item) => (
            <button key={item.id} onClick={() => handleNavigate(item.id)}
              className="flex-1 flex flex-col items-center gap-0.5 py-3 transition-colors"
              style={{ color: page === item.id ? '#0F172A' : '#94A3B8' }}>
              <span className="text-lg leading-none">{item.icon}</span>
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Quick Add Modal */}
      {quickAddOpen && <QuickAdd onClose={() => setQuickAddOpen(false)} onNavigate={handleNavigate} />}

      {/* QA Panel — muncul di pojok bawah (development only) */}
      <QAPanel />
    </div>
    </ToastProvider>
  );
}
