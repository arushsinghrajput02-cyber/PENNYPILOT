/**
 * PennyPilot Authentication & Session State Management
 */

// Route Guard & Profile Initialization
document.addEventListener('DOMContentLoaded', async () => {
  const currentPath = window.location.pathname;
  const isAuthPage = currentPath.endsWith('login.html') || currentPath.endsWith('register.html') || currentPath.endsWith('index.html') || currentPath === '/';
  const token = getToken();

  if (!token && !isAuthPage) {
    window.location.href = 'login.html';
    return;
  }

  if (token && (currentPath.endsWith('login.html') || currentPath.endsWith('register.html'))) {
    window.location.href = 'dashboard.html';
    return;
  }

  // Populate authenticated user info in sidebar if present
  if (token && !isAuthPage) {
    try {
      const user = await apiRequest('/auth/me');
      setUser(user);
      renderSidebarProfile(user);
    } catch (e) {
      console.warn('Failed to refresh user profile:', e);
    }
  }

  // Mobile menu drawer toggle
  const mobileToggle = document.getElementById('mobileMenuToggle');
  const sidebar = document.querySelector('.sidebar');
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-open');
    });
  }
});

function renderSidebarProfile(user) {
  const nameEl = document.getElementById('sidebarUserName');
  const avatarEl = document.getElementById('sidebarUserAvatar');
  if (nameEl && user) {
    nameEl.textContent = user.name;
  }
  if (avatarEl && user) {
    const initials = user.name
      .split(' ')
      .map(part => part[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
    avatarEl.textContent = initials || 'ST';
  }
}

// User Actions
async function loginUser(email, password) {
  try {
    const res = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    setToken(res.access_token);
    setUser(res.user);
    showToast('Signed in successfully! Welcome back.', 'success');
    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 600);
  } catch (err) {
    showToast(err.message || 'Login failed. Please check your credentials.', 'error');
    throw err;
  }
}

async function registerUser(name, email, password) {
  try {
    const res = await apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password })
    });
    setToken(res.access_token);
    setUser(res.user);
    showToast('Account created successfully! Welcome to PennyPilot.', 'success');
    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 600);
  } catch (err) {
    showToast(err.message || 'Registration failed.', 'error');
    throw err;
  }
}

function logoutUser() {
  clearAuth();
  showToast('Logged out successfully.', 'info');
  setTimeout(() => {
    window.location.href = 'login.html';
  }, 400);
}

// 1-Click Demo Student Access
async function demoLogin() {
  try {
    showToast('Loading pre-configured demo student environment...', 'info');
    const res = await apiRequest('/demo/login-demo', { method: 'POST' });
    setToken(res.access_token);
    setUser(res.user);
    showToast('Welcome to Demo Mode, Alex! Enjoy exploring PennyPilot.', 'success');
    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 500);
  } catch (err) {
    showToast('Could not launch demo mode: ' + err.message, 'error');
  }
}

// Seed Demo Data for currently logged-in account
async function seedDemoDataForUser() {
  try {
    const confirmed = confirm('This will load realistic sample student transactions and budgets into your account. Proceed?');
    if (!confirmed) return;
    
    await apiRequest('/demo/seed', { method: 'POST' });
    showToast('Sample student data loaded successfully!', 'success');
    setTimeout(() => {
      window.location.reload();
    }, 600);
  } catch (err) {
    showToast('Failed to seed sample data: ' + err.message, 'error');
  }
}

// Update Emergency Reserve for Survival Mode
async function updateEmergencyReserve(newAmount) {
  try {
    const updated = await apiRequest('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify({ monthly_reserved_amount: Number(newAmount) })
    });
    setUser(updated);
    showToast('Survival Mode reserve amount updated!', 'success');
    return updated;
  } catch (err) {
    showToast('Failed to update reserve: ' + err.message, 'error');
    throw err;
  }
}
