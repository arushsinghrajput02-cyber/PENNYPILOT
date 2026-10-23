/**
 * PennyPilot Main Dashboard Controller
 */

let trendChartInstance = null;
let categoryChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!getToken()) return;

  setupMonthSelector();
  await loadDashboardData();
  setupReserveModal();
  setupQuickTransactionModal();
});

function setupMonthSelector() {
  const select = document.getElementById('dashboardMonthSelect');
  if (!select) return;

  const now = new Date();
  select.innerHTML = '';

  // Generate options for past 5 months and current month
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
    await loadDashboardData();
  });
}

function getSelectedMonthAndYear() {
  const select = document.getElementById('dashboardMonthSelect');
  if (select && select.value) {
    const [y, m] = select.value.split('-').map(Number);
    return { month: m, year: y };
  }
  const now = new Date();
  return { month: now.getMonth() + 1, year: now.getFullYear() };
}

async function loadDashboardData() {
  const { month, year } = getSelectedMonthAndYear();

  try {
    // Parallel fetch for high performance
    const [
      overview,
      survival,
      insights,
      forecast,
      score,
      needsWants,
      categories,
      trends,
      recentTx,
      recurring
    ] = await Promise.all([
      apiRequest(`/analytics/overview?month=${month}&year=${year}`),
      apiRequest(`/analytics/survival-mode?month=${month}&year=${year}`),
      apiRequest(`/analytics/insights?month=${month}&year=${year}`),
      apiRequest(`/analytics/forecast?month=${month}&year=${year}`),
      apiRequest(`/analytics/financial-score?month=${month}&year=${year}`),
      apiRequest(`/analytics/needs-wants?month=${month}&year=${year}`),
      apiRequest(`/analytics/category-breakdown?transaction_type=expense&month=${month}&year=${year}`),
      apiRequest('/analytics/monthly-trend?months_count=6'),
      apiRequest('/transactions?limit=5&sort_by=date&order=desc'),
      apiRequest('/analytics/recurring')
    ]);

    renderKPIs(overview);
    renderSurvivalBanner(survival);
    renderSmartInsights(insights);
    renderForecast(forecast);
    renderHealthScore(score);
    renderNeedsWants(needsWants);
    renderCategoryChart(categories);
    renderTrendChart(trends);
    renderRecentTransactions(recentTx.items || []);
    renderRecurringExpenses(recurring || []);

    initIcons();
  } catch (err) {
    console.error('Error loading dashboard:', err);
    showToast('Failed to load some dashboard widgets: ' + err.message, 'error');
  }
}

// Render Top KPI Stat Cards
function renderKPIs(ov) {
  if (!ov) return;
  document.getElementById('kpiBalance').textContent = formatINR(ov.current_balance);
  document.getElementById('kpiIncome').textContent = formatINR(ov.monthly_income);
  document.getElementById('kpiExpense').textContent = formatINR(ov.monthly_expenses);
  document.getElementById('kpiSavings').textContent = formatINR(ov.monthly_savings);
  document.getElementById('kpiSavingsRate').textContent = `${ov.savings_rate}% saved`;

  const budgetUtilEl = document.getElementById('kpiBudgetUtil');
  const budgetBar = document.getElementById('kpiBudgetBar');
  if (budgetUtilEl && budgetBar) {
    budgetUtilEl.textContent = `${ov.budget_utilization}% of ${formatINR(ov.total_budget, false)}`;
    budgetBar.style.width = `${Math.min(100, ov.budget_utilization)}%`;
    if (ov.budget_utilization >= 100) {
      budgetBar.className = 'progress-bar danger';
    } else if (ov.budget_utilization >= 80) {
      budgetBar.className = 'progress-bar warning';
    } else {
      budgetBar.className = 'progress-bar success';
    }
  }
}

// Render Feature 2: Survival Mode Banner
function renderSurvivalBanner(s) {
  const banner = document.getElementById('survivalBanner');
  if (!banner || !s) return;

  banner.className = `survival-banner status-${s.status}`;
  document.getElementById('survivalDailyLimit').textContent = formatINR(s.suggested_daily_limit, false);
  document.getElementById('survivalDaysRemaining').textContent = `${s.days_remaining_in_month} days`;
  document.getElementById('survivalMessage').textContent = s.message;
  document.getElementById('survivalExplanation').textContent = s.explanation;
  document.getElementById('survivalReservedBadge').textContent = `Reserved: ${formatINR(s.reserved_amount, false)}`;
}

// Render Feature 1: Smart Spend Coach
function renderSmartInsights(insights) {
  const container = document.getElementById('insightsContainer');
  if (!container) return;

  if (!insights || insights.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="padding: 1.5rem;">
        <i data-lucide="sparkles" class="empty-state-icon" style="width: 36px; height: 36px;"></i>
        <div class="empty-state-title">All Good! No Budget Spikes</div>
        <p class="empty-state-text">Spend Coach monitors your daily transactions for anomalies and surges. Keep recording your daily expenses.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = insights.map(item => `
    <div class="insight-card ${item.type}">
      <div class="insight-header">
        <span class="insight-title">${item.title}</span>
        <span class="badge badge-${item.type === 'alert' ? 'danger' : item.type === 'warning' ? 'warning' : 'primary'}">
          ${item.type}
        </span>
      </div>
      <p class="insight-message">${item.message}</p>
      ${item.impact ? `<div class="insight-impact">${item.impact}</div>` : ''}
    </div>
  `).join('');
}

// Render Feature 5: Month-End Forecast
function renderForecast(fc) {
  const el = document.getElementById('forecastProjected');
  const burnEl = document.getElementById('forecastBurnRate');
  const noteEl = document.getElementById('forecastNote');
  if (!el || !fc) return;

  el.textContent = formatINR(fc.projected_end_of_month_spend);
  if (burnEl) burnEl.textContent = `${formatINR(fc.average_daily_burn, false)}/day`;
  if (noteEl) noteEl.textContent = fc.confidence_note;
}

// Render Feature 6: Financial Health Score
function renderHealthScore(score) {
  const numEl = document.getElementById('healthScoreVal');
  const ratingEl = document.getElementById('healthScoreRating');
  const factorsEl = document.getElementById('healthScoreFactors');
  if (!numEl || !score) return;

  numEl.textContent = score.overall_score;
  if (ratingEl) ratingEl.textContent = score.rating;

  if (factorsEl && score.factors) {
    factorsEl.innerHTML = Object.entries(score.factors).map(([key, data]) => `
      <div style="margin-bottom: 0.6rem;">
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 0.2rem;">
          <span style="text-transform: capitalize; font-weight: 600; color: var(--text-main);">${key.replace(/_/g, ' ')}</span>
          <span style="font-weight: 700; color: var(--color-primary);">${data.score}/${data.max}</span>
        </div>
        <div class="progress-container" style="height: 5px;">
          <div class="progress-bar" style="width: ${(data.score / data.max) * 100}%;"></div>
        </div>
        <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 0.15rem;">${data.detail}</div>
      </div>
    `).join('');
  }
}

// Render Feature 3: Needs vs Wants vs Savings
function renderNeedsWants(nw) {
  if (!nw) return;
  const needsPctEl = document.getElementById('nwNeedsPct');
  const wantsPctEl = document.getElementById('nwWantsPct');
  const savingsPctEl = document.getElementById('nwSavingsPct');
  const needsBar = document.getElementById('nwNeedsBar');
  const wantsBar = document.getElementById('nwWantsBar');
  const savingsBar = document.getElementById('nwSavingsBar');

  if (needsPctEl) needsPctEl.textContent = `${nw.needs_percentage}% (${formatINR(nw.needs_amount, false)})`;
  if (wantsPctEl) wantsPctEl.textContent = `${nw.wants_percentage}% (${formatINR(nw.wants_amount, false)})`;
  if (savingsPctEl) savingsPctEl.textContent = `${nw.savings_percentage}% (${formatINR(nw.savings_amount, false)})`;

  if (needsBar) needsBar.style.width = `${nw.needs_percentage}%`;
  if (wantsBar) wantsBar.style.width = `${nw.wants_percentage}%`;
  if (savingsBar) savingsBar.style.width = `${nw.savings_percentage}%`;
}

// Render Category Breakdown Doughnut Chart
function renderCategoryChart(categories) {
  const canvas = document.getElementById('categoryChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  if (!categories || categories.length === 0) {
    // Show placeholder empty canvas or message
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const labels = categories.map(c => c.category);
  const data = categories.map(c => c.amount);
  const palette = [
    '#8B5CF6', '#34D399', '#38BDF8', '#F59E0B', 
    '#F43F5E', '#EC4899', '#A855F7', '#6366F1'
  ];

  categoryChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: palette.slice(0, categories.length),
        borderColor: '#141B2D',
        borderWidth: 3,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94A3B8',
            font: { family: 'Plus Jakarta Sans', size: 11 },
            boxWidth: 12,
            padding: 12
          }
        },
        tooltip: {
          backgroundColor: '#0E1426',
          titleColor: '#F8FAFC',
          bodyColor: '#94A3B8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              return ` ${context.label}: ${formatINR(val)}`;
            }
          }
        }
      },
      cutout: '72%'
    }
  });
}

// Render Monthly Trend Chart
function renderTrendChart(trends) {
  const canvas = document.getElementById('trendChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  if (!trends || trends.length === 0) return;

  const labels = trends.map(t => t.month_name);
  const incomeData = trends.map(t => t.income);
  const expenseData = trends.map(t => t.expenses);

  trendChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Income',
          data: incomeData,
          backgroundColor: 'rgba(52, 211, 153, 0.75)',
          borderRadius: 6,
          barThickness: 16
        },
        {
          label: 'Expenses',
          data: expenseData,
          backgroundColor: 'rgba(139, 92, 246, 0.75)',
          borderRadius: 6,
          barThickness: 16
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#94A3B8', font: { family: 'Plus Jakarta Sans', size: 11 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#94A3B8',
            font: { family: 'Plus Jakarta Sans', size: 11 },
            callback: function(value) {
              return '₹' + (value >= 1000 ? (value / 1000) + 'k' : value);
            }
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            color: '#94A3B8',
            boxWidth: 12,
            font: { family: 'Plus Jakarta Sans', size: 11 }
          }
        },
        tooltip: {
          backgroundColor: '#0E1426',
          titleColor: '#F8FAFC',
          bodyColor: '#94A3B8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: function(context) {
              return ` ${context.dataset.label}: ${formatINR(context.raw)}`;
            }
          }
        }
      }
    }
  });
}

// Render Recent Transactions
function renderRecentTransactions(items) {
  const container = document.getElementById('recentTransactionsTable');
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state" style="padding: 2rem;">
          <div class="empty-state-title">No transactions yet</div>
          <p class="empty-state-text">Click "+ Add Transaction" or "Load Sample Data" to get started.</p>
        </td>
      </tr>
    `;
    return;
  }

  container.innerHTML = items.map(tx => `
    <tr>
      <td>
        <div style="font-weight: 600; color: var(--text-main);">${tx.description || tx.category}</div>
        <div style="font-size: 0.76rem; color: var(--text-dim);">${formatDate(tx.transaction_date)}</div>
      </td>
      <td>
        <span class="badge ${tx.transaction_type === 'income' ? 'badge-success' : 'badge-primary'}">
          ${tx.category}
        </span>
      </td>
      <td>
        <span class="badge badge-info" style="font-size: 0.68rem;">${tx.need_or_want}</span>
      </td>
      <td style="font-weight: 700; text-align: right; color: ${tx.transaction_type === 'income' ? 'var(--color-secondary)' : 'var(--text-main)'};">
        ${tx.transaction_type === 'income' ? '+' : '-'}${formatINR(tx.amount)}
      </td>
    </tr>
  `).join('');
}

// Render Recurring Commitments
function renderRecurringExpenses(items) {
  const container = document.getElementById('recurringList');
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `
      <div style="font-size: 0.85rem; color: var(--text-dim); padding: 0.5rem 0;">
        No recurring student commitments tagged yet (e.g. hostel rent, mess bill).
      </div>
    `;
    return;
  }

  container.innerHTML = items.map(item => `
    <div class="category-item">
      <div>
        <div style="font-weight: 600; color: var(--text-main); font-size: 0.88rem;">${item.description || item.category}</div>
        <div style="font-size: 0.74rem; color: var(--text-dim);">${item.category} • Recurring</div>
      </div>
      <div style="font-weight: 700; color: var(--color-danger); font-size: 0.92rem;">
        ${formatINR(item.amount)}
      </div>
    </div>
  `).join('');
}

// Reserve Modal for Survival Mode
function setupReserveModal() {
  const form = document.getElementById('reserveForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const val = document.getElementById('reserveAmountInput').value;
    await updateEmergencyReserve(val);
    closeModal('reserveModal');
    await loadDashboardData();
  });
}

// Quick Add Transaction Modal Setup
function setupQuickTransactionModal() {
  const form = document.getElementById('quickTransactionForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = Number(document.getElementById('quickTxAmount').value);
    const type = document.getElementById('quickTxType').value;
    const category = document.getElementById('quickTxCategory').value;
    const desc = document.getElementById('quickTxDesc').value;
    const classification = document.getElementById('quickTxClassification').value;
    const dateVal = document.getElementById('quickTxDate').value || new Date().toISOString().split('T')[0];
    const isRecurring = document.getElementById('quickTxRecurring').checked;

    try {
      await apiRequest('/transactions', {
        method: 'POST',
        body: JSON.stringify({
          amount,
          transaction_type: type,
          category,
          description: desc,
          transaction_date: dateVal,
          need_or_want: classification,
          is_recurring: isRecurring
        })
      });
      showToast('Transaction added successfully!', 'success');
      closeModal('quickTransactionModal');
      form.reset();
      await loadDashboardData();
    } catch (err) {
      showToast('Failed to add transaction: ' + err.message, 'error');
    }
  });
}
