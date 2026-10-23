/**
 * PennyPilot Analytics & Reports Controller
 */

let categoryChart = null;
let trendChart = null;
let needsWantsChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!getToken()) return;

  setupMonthSelector();
  await loadAnalytics();
});

function setupMonthSelector() {
  const select = document.getElementById('analyticsMonthSelect');
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
    await loadAnalytics();
  });
}

function getSelectedPeriod() {
  const select = document.getElementById('analyticsMonthSelect');
  if (select && select.value) {
    const [y, m] = select.value.split('-').map(Number);
    return { month: m, year: y };
  }
  const now = new Date();
  return { month: now.getMonth() + 1, year: now.getFullYear() };
}

async function loadAnalytics() {
  const { month, year } = getSelectedPeriod();

  try {
    const [categories, trends, needsWants, overview] = await Promise.all([
      apiRequest(`/analytics/category-breakdown?transaction_type=expense&month=${month}&year=${year}`),
      apiRequest('/analytics/monthly-trend?months_count=6'),
      apiRequest(`/analytics/needs-wants?month=${month}&year=${year}`),
      apiRequest(`/analytics/overview?month=${month}&year=${year}`)
    ]);

    renderOverviewCards(overview);
    renderCategoryDoughnut(categories);
    renderMonthlyTrendChart(trends);
    renderNeedsWantsChart(needsWants);
    renderCategoryTable(categories);
    initIcons();
  } catch (err) {
    showToast('Failed to load analytics: ' + err.message, 'error');
  }
}

function renderOverviewCards(ov) {
  if (!ov) return;
  document.getElementById('analyticsTotalIncome').textContent = formatINR(ov.monthly_income);
  document.getElementById('analyticsTotalExpense').textContent = formatINR(ov.monthly_expenses);
  document.getElementById('analyticsNetSavings').textContent = formatINR(ov.monthly_savings);
  document.getElementById('analyticsSavingsRate').textContent = `${ov.savings_rate}%`;
}

function renderCategoryDoughnut(categories) {
  const canvas = document.getElementById('analyticsCategoryChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (categoryChart) categoryChart.destroy();

  if (!categories || categories.length === 0) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const labels = categories.map(c => c.category);
  const data = categories.map(c => c.amount);
  const colors = [
    '#8B5CF6', '#34D399', '#38BDF8', '#F59E0B', 
    '#F43F5E', '#EC4899', '#A855F7', '#6366F1', '#10B981'
  ];

  categoryChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors.slice(0, categories.length),
        borderColor: '#141B2D',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94A3B8', font: { family: 'Plus Jakarta Sans', size: 12 }, padding: 14 }
        },
        tooltip: {
          callbacks: {
            label: function(ctx) {
              return ` ${ctx.label}: ${formatINR(ctx.raw)}`;
            }
          }
        }
      }
    }
  });
}

function renderMonthlyTrendChart(trends) {
  const canvas = document.getElementById('analyticsTrendChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (trendChart) trendChart.destroy();

  if (!trends || trends.length === 0) return;

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: trends.map(t => t.month_name),
      datasets: [
        {
          label: 'Income',
          data: trends.map(t => t.income),
          borderColor: '#34D399',
          backgroundColor: 'rgba(52, 211, 153, 0.1)',
          tension: 0.35,
          fill: true
        },
        {
          label: 'Expenses',
          data: trends.map(t => t.expenses),
          borderColor: '#8B5CF6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          tension: 0.35,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: '#94A3B8' } },
        y: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: {
            color: '#94A3B8',
            callback: v => '₹' + (v >= 1000 ? (v / 1000) + 'k' : v)
          }
        }
      },
      plugins: {
        legend: { position: 'top', align: 'end', labels: { color: '#94A3B8' } }
      }
    }
  });
}

function renderNeedsWantsChart(nw) {
  const canvas = document.getElementById('analyticsNeedsWantsChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (needsWantsChart) needsWantsChart.destroy();

  needsWantsChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Needs (Essentials)', 'Wants (Discretionary)', 'Savings'],
      datasets: [{
        data: [nw.needs_amount, nw.wants_amount, nw.savings_amount],
        backgroundColor: ['#38BDF8', '#F59E0B', '#34D399'],
        borderColor: '#141B2D',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94A3B8', padding: 12 } },
        tooltip: {
          callbacks: {
            label: function(ctx) {
              return ` ${ctx.label}: ${formatINR(ctx.raw)}`;
            }
          }
        }
      },
      cutout: '65%'
    }
  });
}

function renderCategoryTable(categories) {
  const tbody = document.getElementById('categoryBreakdownTableBody');
  if (!tbody) return;

  if (categories.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state" style="padding: 2rem;">No expenses logged for this month.</td></tr>`;
    return;
  }

  tbody.innerHTML = categories.map(c => `
    <tr>
      <td style="font-weight: 600; color: var(--text-main);">${c.category}</td>
      <td style="text-align: right; font-weight: 700;">${formatINR(c.amount)}</td>
      <td style="text-align: right; color: var(--text-muted);">${c.percentage}%</td>
      <td style="text-align: right; color: var(--text-dim);">${c.count} transactions</td>
    </tr>
  `).join('');
}
