/**
 * PennyPilot Budgets Controller
 */

let activeBudgets = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!getToken()) return;

  setupMonthSelector();
  setupBudgetModal();
  await loadBudgets();
});

function setupMonthSelector() {
  const select = document.getElementById('budgetMonthSelect');
  if (!select) return;

  const now = new Date();
  select.innerHTML = '';
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const m = d.getMonth() + 1;
    const y = d.getFullYear();
    const opt = document.createElement('option');
    opt.value = `${y}-${m}`;
    opt.textContent = d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
    if (i === 0) opt.selected = true;
    select.appendChild(opt);
  }

  select.addEventListener('change', async () => {
    await loadBudgets();
  });
}

function getSelectedPeriod() {
  const select = document.getElementById('budgetMonthSelect');
  if (select && select.value) {
    const [y, m] = select.value.split('-').map(Number);
    return { month: m, year: y };
  }
  const now = new Date();
  return { month: now.getMonth() + 1, year: now.getFullYear() };
}

async function loadBudgets() {
  const { month, year } = getSelectedPeriod();

  try {
    const summary = await apiRequest(`/budgets/summary?month=${month}&year=${year}`);
    activeBudgets = summary.items || [];
    renderBudgetSummary(summary);
    renderBudgetCircles(activeBudgets);
    initIcons();
  } catch (err) {
    showToast('Failed to load budgets: ' + err.message, 'error');
  }
}

function renderBudgetSummary(summary) {
  const overallLimitEl = document.getElementById('overallBudgetLimit');
  const overallSpentEl = document.getElementById('overallBudgetSpent');
  const overallRemEl = document.getElementById('overallBudgetRemaining');
  const overallPctEl = document.getElementById('overallBudgetPct');
  const overallBar = document.getElementById('overallProgressBar');
  const alertBox = document.getElementById('budgetStatusAlert');

  if (!overallLimitEl) return;

  overallLimitEl.textContent = formatINR(summary.total_budget, false);
  overallSpentEl.textContent = formatINR(summary.total_spent, false);
  const remaining = Math.max(0, summary.total_budget - summary.total_spent);
  overallRemEl.textContent = formatINR(remaining, false);
  overallPctEl.textContent = `${summary.overall_percentage}%`;

  if (overallBar) {
    overallBar.style.width = `${Math.min(100, summary.overall_percentage)}%`;
    if (summary.status === 'exceeded') {
      overallBar.className = 'progress-bar danger';
    } else if (summary.status === 'warning') {
      overallBar.className = 'progress-bar warning';
    } else {
      overallBar.className = 'progress-bar success';
    }
  }

  if (alertBox) {
    if (summary.status === 'exceeded') {
      alertBox.style.display = 'block';
      alertBox.className = 'card';
      alertBox.style.borderColor = 'var(--color-danger)';
      alertBox.style.background = 'rgba(244, 63, 94, 0.1)';
      alertBox.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem; color: var(--color-danger);">
          <i data-lucide="alert-octagon"></i>
          <div>
            <strong>Monthly Budget Exceeded!</strong>
            <div style="font-size: 0.85rem; color: var(--text-main);">You have outspent your allocated budget limit by ${formatINR(summary.total_spent - summary.total_budget)}. Switch to Survival Mode to manage till month end.</div>
          </div>
        </div>
      `;
    } else if (summary.status === 'warning') {
      alertBox.style.display = 'block';
      alertBox.className = 'card';
      alertBox.style.borderColor = 'var(--color-warning)';
      alertBox.style.background = 'rgba(245, 158, 11, 0.1)';
      alertBox.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem; color: #FBBF24;">
          <i data-lucide="alert-triangle"></i>
          <div>
            <strong>Budget Usage Alert (80% Reached)</strong>
            <div style="font-size: 0.85rem; color: var(--text-main);">You have utilized ${summary.overall_percentage}% of your monthly funds. Consider pausing discretionary spends.</div>
          </div>
        </div>
      `;
    } else {
      alertBox.style.display = 'none';
    }
  }
}

function renderBudgetCircles(items) {
  const grid = document.getElementById('categoryBudgetsGrid');
  if (!grid) return;

  const categoryBudgets = items.filter(b => b.category !== 'Overall');

  if (categoryBudgets.length === 0) {
    grid.innerHTML = `
      <div class="card empty-state" style="grid-column: 1 / -1;">
        <i data-lucide="pie-chart" class="empty-state-icon"></i>
        <div class="empty-state-title">No category-specific budgets set</div>
        <p class="empty-state-text">Allocating limits for food, entertainment, and books prevents unexpected overdrafts.</p>
        <button class="btn btn-primary" onclick="openAddBudgetModal()">Set Category Budget</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = categoryBudgets.map(b => {
    let barColor = 'success';
    if (b.status === 'exceeded') barColor = 'danger';
    else if (b.status === 'warning') barColor = 'warning';

    return `
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <span>${b.category}</span>
          </div>
          <span class="badge ${b.status === 'exceeded' ? 'badge-danger' : b.status === 'warning' ? 'badge-warning' : 'badge-success'}">
            ${b.percentage_used}% used
          </span>
        </div>

        <div style="margin-bottom: 0.8rem;">
          <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
            <span style="color: var(--text-muted);">Spent: ${formatINR(b.spent_amount)}</span>
            <span style="font-weight: 700; color: var(--text-main);">Limit: ${formatINR(b.monthly_limit, false)}</span>
          </div>
          <div class="progress-container">
            <div class="progress-bar ${barColor}" style="width: ${Math.min(100, b.percentage_used)}%;"></div>
          </div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: var(--text-dim); margin-top: 0.5rem;">
          <span>${b.remaining_amount >= 0 ? `Remaining: ${formatINR(b.remaining_amount)}` : `Over by: ${formatINR(Math.abs(b.remaining_amount))}`}</span>
          <button class="btn btn-outline btn-sm" onclick="deleteBudgetItem(${b.id})" style="padding: 0.25rem 0.5rem; color: var(--color-danger); border-color: rgba(244,63,94,0.3);">
            <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function setupBudgetModal() {
  const form = document.getElementById('budgetForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const category = document.getElementById('budgetCategory').value;
    const limit = Number(document.getElementById('budgetLimit').value);
    const { month, year } = getSelectedPeriod();

    try {
      await apiRequest('/budgets', {
        method: 'POST',
        body: JSON.stringify({
          category,
          monthly_limit: limit,
          month,
          year
        })
      });
      showToast('Budget saved successfully!', 'success');
      closeModal('budgetModal');
      form.reset();
      await loadBudgets();
    } catch (err) {
      showToast('Failed to save budget: ' + err.message, 'error');
    }
  });
}

function openAddBudgetModal(defaultCategory = null) {
  const form = document.getElementById('budgetForm');
  if (form) form.reset();
  if (defaultCategory) {
    const catSelect = document.getElementById('budgetCategory');
    if (catSelect) catSelect.value = defaultCategory;
  }
  openModal('budgetModal');
}

async function deleteBudgetItem(budgetId) {
  if (!confirm('Are you sure you want to remove this budget?')) return;
  try {
    await apiRequest(`/budgets/${budgetId}`, { method: 'DELETE' });
    showToast('Budget deleted.', 'info');
    await loadBudgets();
  } catch (err) {
    showToast('Failed to delete: ' + err.message, 'error');
  }
}
