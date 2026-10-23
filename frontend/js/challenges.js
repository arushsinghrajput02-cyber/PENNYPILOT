/**
 * PennyPilot No-Spend Challenges Controller
 */

let challengesList = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!getToken()) return;

  setupChallengeModal();
  await loadChallenges();
});

async function loadChallenges() {
  try {
    challengesList = await apiRequest('/challenges');
    renderChallenges(challengesList);
    initIcons();
  } catch (err) {
    showToast('Failed to load challenges: ' + err.message, 'error');
  }
}

function renderChallenges(items) {
  const grid = document.getElementById('challengesGrid');
  if (!grid) return;

  if (items.length === 0) {
    grid.innerHTML = `
      <div class="card empty-state" style="grid-column: 1 / -1;">
        <i data-lucide="shield-check" class="empty-state-icon"></i>
        <div class="empty-state-title">No Active Challenges</div>
        <p class="empty-state-text">Commit to a 7-day challenge to break unnecessary spending habits and save cash for what really matters.</p>
        <button class="btn btn-primary" onclick="openModal('challengeModal')">Start a Challenge</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = items.map(c => {
    const isCompleted = c.status === 'completed';
    const isFailed = c.status === 'failed' || (!c.is_on_track && c.days_left === 0);
    const onTrack = c.is_on_track;

    let badgeClass = 'badge-primary';
    let statusText = `${c.days_left}d remaining`;

    if (isCompleted) {
      badgeClass = 'badge-success';
      statusText = 'Completed 🏆';
    } else if (isFailed) {
      badgeClass = 'badge-danger';
      statusText = 'Limit Breached ❌';
    } else if (onTrack) {
      badgeClass = 'badge-success';
      statusText = `On Track • ${c.days_left}d left`;
    } else {
      badgeClass = 'badge-danger';
      statusText = `Over Limit • ${c.days_left}d left`;
    }

    return `
      <div class="card" style="border-left: 4px solid ${onTrack ? 'var(--color-secondary)' : 'var(--color-danger)'};">
        <div class="card-header">
          <div>
            <span class="badge ${badgeClass}">${statusText}</span>
            <h3 style="margin-top: 0.4rem; font-size: 1.15rem;">${c.title}</h3>
          </div>
          <span class="badge badge-info">${c.category}</span>
        </div>

        <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1rem;">
          ${c.description || 'Discipline challenge tracked against your real transactions.'}
        </p>

        <div style="background: var(--bg-surface); padding: 0.85rem 1rem; border-radius: var(--radius-md); margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.25rem;">
            <span style="color: var(--text-dim); font-weight: 600;">Spending Cap:</span>
            <span style="font-weight: 700; color: var(--text-main);">${formatINR(c.target_amount, false)}</span>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.82rem;">
            <span style="color: var(--text-dim); font-weight: 600;">Actual Spend Logged:</span>
            <span style="font-weight: 800; color: ${onTrack ? 'var(--color-secondary)' : 'var(--color-danger)'};">
              ${formatINR(c.current_spent)}
            </span>
          </div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: var(--text-dim);">
          <span>Period: ${formatDate(c.start_date)} - ${formatDate(c.end_date)}</span>
          <button class="btn btn-outline btn-sm" onclick="deleteChallengeItem(${c.id})" style="color: var(--color-danger); border-color: rgba(244,63,94,0.3);">
            <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function setupChallengeModal() {
  const form = document.getElementById('challengeForm');
  if (!form) return;

  // Set default dates: today to +7 days
  const todayStr = new Date().toISOString().split('T')[0];
  const nextWeek = new Date();
  nextWeek.setDate(nextWeek.getDate() + 7);
  const nextWeekStr = nextWeek.toISOString().split('T')[0];

  const startInput = document.getElementById('challengeStart');
  const endInput = document.getElementById('challengeEnd');
  if (startInput) startInput.value = todayStr;
  if (endInput) endInput.value = nextWeekStr;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('challengeTitle').value;
    const desc = document.getElementById('challengeDesc').value;
    const category = document.getElementById('challengeCategory').value;
    const target = Number(document.getElementById('challengeTarget').value);
    const start = document.getElementById('challengeStart').value;
    const end = document.getElementById('challengeEnd').value;

    try {
      await apiRequest('/challenges', {
        method: 'POST',
        body: JSON.stringify({
          title,
          description: desc,
          category,
          target_amount: target,
          start_date: start,
          end_date: end
        })
      });
      showToast('New spending challenge launched!', 'success');
      closeModal('challengeModal');
      form.reset();
      await loadChallenges();
    } catch (err) {
      showToast('Failed to start challenge: ' + err.message, 'error');
    }
  });
}

function selectPreset(type) {
  const title = document.getElementById('challengeTitle');
  const desc = document.getElementById('challengeDesc');
  const cat = document.getElementById('challengeCategory');
  const target = document.getElementById('challengeTarget');

  if (type === 'food') {
    title.value = '7-Day Zero Food Delivery';
    desc.value = 'Stick to hostel mess or home cooking. No Swiggy or Zomato orders.';
    cat.value = 'Food & Dining';
    target.value = 0;
  } else if (type === 'shopping') {
    title.value = '10-Day No Online Shopping';
    desc.value = 'Zero ecommerce or tech accessory purchases for the next 10 days.';
    cat.value = 'All Non-Essentials';
    target.value = 0;
  } else if (type === 'weekend') {
    title.value = 'Weekend Budget Cap < ₹500';
    desc.value = 'Keep all cafe hangouts and entertainment strictly under ₹500.';
    cat.value = 'All Non-Essentials';
    target.value = 500;
  }
}

async function deleteChallengeItem(id) {
  if (!confirm('Are you sure you want to remove this challenge?')) return;
  try {
    await apiRequest(`/challenges/${id}`, { method: 'DELETE' });
    showToast('Challenge removed.', 'info');
    await loadChallenges();
  } catch (err) {
    showToast('Failed to delete challenge: ' + err.message, 'error');
  }
}
