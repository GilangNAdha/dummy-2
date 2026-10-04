export const categories = [
  { name: 'Makanan & Minuman', icon: '🍽️', color: '#F59E0B' },
  { name: 'Transportasi', icon: '🚗', color: '#3B82F6' },
  { name: 'Belanja', icon: '🛍️', color: '#EC4899' },
  { name: 'Pendidikan', icon: '📚', color: '#8B5CF6' },
  { name: 'Kesehatan', icon: '💊', color: '#10B981' },
  { name: 'Tagihan & Utilitas', icon: '💡', color: '#F97316' },
  { name: 'Hiburan', icon: '🎬', color: '#06B6D4' },
  { name: 'Lainnya', icon: '📦', color: '#94A3B8' },
];

export const members = ['Ayah', 'Ibu', 'Anak'];

export const accounts = ['BCA Utama', 'Mandiri Tabungan', 'Tunai', 'GoPay', 'OVO'];

export const mockAccounts = [
  { id: '1', name: 'BCA Utama',        icon: '🏦', type: 'bank',    balance: 8500000  },
  { id: '2', name: 'Mandiri Tabungan', icon: '🏦', type: 'bank',    balance: 12300000 },
  { id: '3', name: 'Tunai',            icon: '💵', type: 'cash',    balance: 750000   },
  { id: '4', name: 'GoPay',            icon: '🟢', type: 'ewallet', balance: 320000   },
  { id: '5', name: 'OVO',              icon: '🟣', type: 'ewallet', balance: 185000   },
];

export const transactions = [
  { id: '1', date: '2024-01-15', type: 'expense', amount: 250000, category: 'Makanan & Minuman', member: 'Ibu', merchant: 'Pasar Minggu', notes: 'Belanja sayur dan lauk', account: 'Tunai' },
  { id: '2', date: '2024-01-15', type: 'expense', amount: 85000, category: 'Transportasi', member: 'Ayah', merchant: 'Pertamina SPBU', notes: 'Isi bensin', account: 'BCA Utama' },
  { id: '3', date: '2024-01-14', type: 'income', amount: 12500000, category: 'Lainnya', member: 'Ayah', merchant: 'PT Maju Bersama', notes: 'Gaji Januari', account: 'BCA Utama' },
  { id: '4', date: '2024-01-14', type: 'expense', amount: 350000, category: 'Pendidikan', member: 'Anak', merchant: 'Gramedia', notes: 'Buku pelajaran semester 2', account: 'BCA Utama' },
  { id: '5', date: '2024-01-13', type: 'expense', amount: 450000, category: 'Tagihan & Utilitas', member: 'Ayah', merchant: 'PLN', notes: 'Tagihan listrik Januari', account: 'Mandiri Tabungan' },
  { id: '6', date: '2024-01-13', type: 'expense', amount: 180000, category: 'Belanja', member: 'Ibu', merchant: 'Indomaret', notes: 'Kebutuhan rumah tangga', account: 'GoPay' },
  { id: '7', date: '2024-01-12', type: 'expense', amount: 120000, category: 'Hiburan', member: 'Anak', merchant: 'Cinema XXI', notes: 'Nonton film bareng teman', account: 'OVO' },
  { id: '8', date: '2024-01-12', type: 'income', amount: 8500000, category: 'Lainnya', member: 'Ibu', merchant: 'PT Sejahtera', notes: 'Gaji Januari Ibu', account: 'Mandiri Tabungan' },
  { id: '9', date: '2024-01-11', type: 'expense', amount: 275000, category: 'Kesehatan', member: 'Ayah', merchant: 'Apotek Kimia Farma', notes: 'Obat dan vitamin', account: 'BCA Utama' },
  { id: '10', date: '2024-01-11', type: 'transfer', amount: 2000000, category: 'Lainnya', member: 'Ayah', merchant: 'Transfer Antar Rekening', notes: 'Tabungan bulanan', account: 'BCA Utama' },
  { id: '11', date: '2024-01-10', type: 'expense', amount: 65000, category: 'Makanan & Minuman', member: 'Anak', merchant: 'Kafe Bumi', notes: 'Makan siang', account: 'OVO' },
  { id: '12', date: '2024-01-10', type: 'expense', amount: 320000, category: 'Transportasi', member: 'Ibu', merchant: 'Grab', notes: 'Ojek online minggu ini', account: 'GoPay' },
  { id: '13', date: '2024-01-09', type: 'expense', amount: 599000, category: 'Tagihan & Utilitas', member: 'Ayah', merchant: 'Telkomsel', notes: 'Paket internet bulanan', account: 'BCA Utama' },
  { id: '14', date: '2024-01-08', type: 'expense', amount: 175000, category: 'Makanan & Minuman', member: 'Ibu', merchant: 'Warung Bu Sari', notes: 'Makan malam keluarga', account: 'Tunai' },
];

export const budgets = [
  { category: 'Makanan & Minuman', icon: '🍽️', color: '#F59E0B', limit: 3000000, spent: 1890000 },
  { category: 'Transportasi', icon: '🚗', color: '#3B82F6', limit: 1500000, spent: 1105000 },
  { category: 'Belanja', icon: '🛍️', color: '#EC4899', limit: 1000000, spent: 680000 },
  { category: 'Pendidikan', icon: '📚', color: '#8B5CF6', limit: 800000, spent: 350000 },
  { category: 'Kesehatan', icon: '💊', color: '#10B981', limit: 500000, spent: 275000 },
  { category: 'Tagihan & Utilitas', icon: '💡', color: '#F97316', limit: 1200000, spent: 1049000 },
  { category: 'Hiburan', icon: '🎬', color: '#06B6D4', limit: 600000, spent: 120000 },
];

export const goals = [
  { id: '1', name: 'Dana Darurat', target: 50000000, current: 32500000, deadline: '2024-12-31', icon: '🛡️', color: '#10B981' },
  { id: '2', name: 'Liburan Keluarga', target: 15000000, current: 7800000, deadline: '2024-07-31', icon: '✈️', color: '#3B82F6' },
  { id: '3', name: 'Renovasi Rumah', target: 30000000, current: 12000000, deadline: '2025-06-30', icon: '🏠', color: '#8B5CF6' },
  { id: '4', name: 'Motor Baru', target: 25000000, current: 5600000, deadline: '2025-03-31', icon: '🏍️', color: '#F59E0B' },
];

export function formatRupiah(amount) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}
