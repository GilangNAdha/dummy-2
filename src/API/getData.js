// getData.js — lapisan data fetching
// Saat ini: ambil dari localStorage (dengan fallback ke mockData)
// Nanti ganti dengan: import axios from 'axios'; dan panggil endpoint FastAPI

import { load, save } from '../utils/localStorage';
import { track } from '../utils/analytics';
import {
  transactions as mockTransactions,
  budgets as mockBudgets,
  goals as mockGoals,
  categories as mockCategories,
  mockAccounts,
} from '../data/mockData';

// const BASE_URL = 'http://localhost:8000/api'; // aktifkan saat backend siap

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

  // Nanti ganti dengan:
  // const { data } = await axios.get(`${BASE_URL}/categories`);
  // return data;

  const cached = load('kf_categories', null);
  if (cached) return cached;

  await simulateDelay();
  save('kf_categories', mockCategories);
  return mockCategories;
}

export async function postCategory(cat) {
  track('getData:postCategory', { name: cat.name });

  // Nanti ganti dengan:
  // const { data } = await axios.post(`${BASE_URL}/categories`, cat);
  // return data;

  const current = load('kf_categories', mockCategories);
  const updated = [...current, cat];
  save('kf_categories', updated);
  return updated;
}

export async function putCategory(name, changes) {
  track('getData:putCategory', { name });

  // Nanti ganti dengan:
  // const { data } = await axios.put(`${BASE_URL}/categories/${name}`, changes);
  // return data;

  const current = load('kf_categories', mockCategories);
  const updated = current.map(c => c.name === name ? { ...c, ...changes } : c);
  save('kf_categories', updated);
  return updated;
}

// ─── Accounts ────────────────────────────────────────────────

export async function getAccounts() {
  track('getData:getAccounts');

  // Nanti ganti dengan:
  // const { data } = await axios.get(`${BASE_URL}/accounts`);
  // return data;

  const cached = load('kf_accounts', null);
  if (cached) return cached;

  await simulateDelay();
  save('kf_accounts', mockAccounts);
  return mockAccounts;
}

export async function postAccount(acc) {
  track('getData:postAccount', { name: acc.name });

  // Nanti ganti dengan:
  // const { data } = await axios.post(`${BASE_URL}/accounts`, acc);
  // return data;

  const current = load('kf_accounts', mockAccounts);
  const updated = [...current, acc];
  save('kf_accounts', updated);
  return updated;
}

export async function putAccount(id, changes) {
  track('getData:putAccount', { id });

  // Nanti ganti dengan:
  // const { data } = await axios.put(`${BASE_URL}/accounts/${id}`, changes);
  // return data;

  const current = load('kf_accounts', mockAccounts);
  const updated = current.map(a => a.id === id ? { ...a, ...changes } : a);
  save('kf_accounts', updated);
  return updated;
}

export async function deleteAccount(id) {
  track('getData:deleteAccount', { id });

  // Nanti ganti dengan:
  // await axios.delete(`${BASE_URL}/accounts/${id}`);

  const current = load('kf_accounts', mockAccounts);
  const updated = current.filter(a => a.id !== id);
  save('kf_accounts', updated);
  return updated;
}

// ─── Helper ──────────────────────────────────────────────────

function simulateDelay(ms = 400) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
