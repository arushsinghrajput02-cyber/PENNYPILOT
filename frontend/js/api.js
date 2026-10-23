/**
 * PennyPilot API Client & Frontend Utilities
 */

const API_BASE = window.location.origin.includes(':8000') 
  ? `${window.location.origin}/api` 
  : 'http://127.0.0.1:8000/api';

const TOKEN_KEY = 'pennypilot_jwt_token';
const USER_KEY = 'pennypilot_user';

// Token helpers
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function getUser() {
  const u = localStorage.getItem(USER_KEY);
  return u ? JSON.parse(u) : null;
}

function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// Core API Request Wrapper
async function apiRequest(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, { ...options, headers });

    // Handle session expiry or unauthorized
    if (res.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/demo/login-demo')) {
      clearAuth();
      if (!window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('index.html')) {
        window.location.href = 'login.html?expired=true';
      }
      throw new Error('Your session has expired. Please sign in again.');
    }

    if (res.status === 204) {
      return null;
    }

    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'An unexpected error occurred');
      }
      return data;
    }

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || 'An unexpected error occurred');
    }

    return res;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

// Indian Rupee Currency Formatter
function formatINR(amount, includeDecimals = true) {
  if (amount === null || amount === undefined || isNaN(amount)) return '₹0';
  const num = Number(amount);
  const isNegative = num < 0;
  const absNum = Math.abs(num);

  // Format with standard Indian numbering system
  const formatted = absNum.toLocaleString('en-IN', {
    maximumFractionDigits: includeDecimals ? 2 : 0,
    minimumFractionDigits: includeDecimals ? 2 : 0
  });

  return `${isNegative ? '-' : ''}₹${formatted}`;
}

// Human-friendly Date Formatter
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
}

// Notification Toast Utility
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Modal Controllers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Safe Lucide icon initializer
function initIcons() {
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
}

// Close modal when clicking outside container
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});
