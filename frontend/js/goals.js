/**
 * PennyPilot Savings Goals Controller
 */

let activeGoals = [];
let targetDepositGoalId = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!getToken()) return;

  setupGoalModal();
  setupDepositModal();
  await loadGoals();
});

async function loadGoals() {
  try {
    const goals = await apiRequest('/goals');
    activeGoals = goals || [];
    renderGoalsList(activeGoals);
    initIcons();
  } catch (err) {
    showToast('Failed to load savings goals: ' + err.message, 'error');
  }
}

function renderGoalsList(goals) {
  const grid = document.getElementById('goalsGrid');
  if (!grid) return;

  if (goals.length === 0) {
    grid.innerHTML = `
      <div class="card empty-state" style="grid-column: 1 / -1;">
        <i data-lucide="target" class="empty-state-icon"></i>
        <div class="empty-state-title">No Savings Goals Yet</div>
        <p class="empty-state-text">Whether it's a new laptop for coding, semester exam fees, or a graduation trip, start with small daily or weekly deposits.</p>
        <button class="btn btn-primary" onclick="openModal('goalModal')">+ Create Your First Goal</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = goals.map(g => {
    const isCompleted = g.status === 'completed' || g.current_amount >= g.target_amount;
    return `
      <div class="card">
        <div class="card-header">
          <div>
            <span class="badge ${isCompleted ? 'badge-success' : 'badge-primary'}">${g.category}</span>
            <h3 style="margin-top: 0.4rem; font-size: 1.15rem;">${g.title}</h3>
          </div>
          <span class="badge ${isCompleted ? 'badge-success' : 'badge-info'}">
            ${isCompleted ? 'Goal Reached 🎉' : `${g.days_remaining > 0 ? `${g.days_remaining}d left` : 'Due'}`}
          </span>
        </div>

        <div style="margin: 1rem 0;">
          <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.35rem;">
            <span style="font-size: 1.5rem; font-weight: 800; color: ${isCompleted ? 'var(--color-secondary)' : 'var(--text-main)'};">
              ${formatINR(g.current_amount)}
            </span>
            <span style="font-size: 0.85rem; color: var(--text-dim); font-weight: 600;">
              Target: ${formatINR(g.target_amount, false)}
            </span>
          </div>

          <div class="progress-container" style="height: 10px;">
            <div class="progress-bar ${isCompleted ? 'success' : ''}" style="width: ${Math.min(100, g.percentage_complete)}%;"></div>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--text-muted); margin-top: 0.35rem;">
            <span>${g.percentage_complete}% reached</span>
            <span>${isCompleted ? 'Fully Funded' : `Remaining: ${formatINR(g.remaining_amount)}`}</span>
          </div>
        </div>

        <div style="font-size: 0.8rem; color: var(--text-dim); margin-bottom: 1rem;">
          Target Date: <strong>${formatDate(g.target_date)}</strong>
        </div>

        <div style="display: flex; gap: 0.5rem; justify-content: space-between; border-top: 1px solid var(--border-subtle); padding-top: 1rem;">
          <button class="btn btn-outline btn-sm" onclick="openDepositModal(${g.id}, '${escapeQuotes(g.title)}')">
            <i data-lucide="plus-circle" style="width: 14px; height: 14px;"></i> Deposit Funds
          </button>
          <button class="btn btn-outline btn-sm" onclick="deleteGoalItem(${g.id})" style="color: var(--color-danger); border-color: rgba(244,63,94,0.3);">
            <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function escapeQuotes(str) {
  return (str || '').replace(/'/g, "\\'");
}

function setupGoalModal() {
  const form = document.getElementById('goalForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('goalTitle').value;
    const target = Number(document.getElementById('goalTarget').value);
    const dateVal = document.getElementById('goalDate').value;
    const category = document.getElementById('goalCategory').value;
    const initial = Number(document.getElementById('goalInitial').value) || 0;

    try {
      await apiRequest('/goals', {
        method: 'POST',
        body: JSON.stringify({
          title,
          target_amount: target,
          target_date: dateVal,
          category,
          initial_deposit: initial
        })
      });
      showToast('Savings goal created!', 'success');
      closeModal('goalModal');
      form.reset();
      await loadGoals();
    } catch (err) {
      showToast('Failed to create goal: ' + err.message, 'error');
    }
  });
}

function openDepositModal(goalId, title) {
  targetDepositGoalId = goalId;
  const titleEl = document.getElementById('depositGoalTitle');
  if (titleEl) titleEl.textContent = title;
  const form = document.getElementById('depositForm');
  if (form) form.reset();
  openModal('depositModal');
}

function setupDepositModal() {
  const form = document.getElementById('depositForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!targetDepositGoalId) return;

    const amount = Number(document.getElementById('depositAmount').value);
    const note = document.getElementById('depositNote').value;

    try {
      await apiRequest(`/goals/${targetDepositGoalId}/contribute`, {
        method: 'POST',
        body: JSON.stringify({ amount, note })
      });
      showToast(`Deposited ${formatINR(amount)} into savings goal!`, 'success');
      closeModal('depositModal');
      targetDepositGoalId = null;
      await loadGoals();
    } catch (err) {
      showToast('Deposit failed: ' + err.message, 'error');
    }
  });
}

async function deleteGoalItem(goalId) {
  if (!confirm('Are you sure you want to delete this savings goal?')) return;
  try {
    await apiRequest(`/goals/${goalId}`, { method: 'DELETE' });
    showToast('Goal deleted.', 'info');
    await loadGoals();
  } catch (err) {
    showToast('Failed to delete goal: ' + err.message, 'error');
  }
}
