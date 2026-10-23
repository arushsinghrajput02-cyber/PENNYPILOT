/**
 * PennyPilot Transactions Controller
 */

let currentPage = 1;
const PAGE_SIZE = 12;
let searchDebounceTimeout = null;
let currentEditingTxId = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!getToken()) return;

  setupFilters();
  setupAddEditModal();
  setupDeleteModal();
  await loadTransactions();
});

function setupFilters() {
  const searchInput = document.getElementById('searchQuery');
  const typeFilter = document.getElementById('typeFilter');
  const categoryFilter = document.getElementById('categoryFilter');
  const classificationFilter = document.getElementById('classificationFilter');
  const sortFilter = document.getElementById('sortFilter');
  const exportBtn = document.getElementById('exportCsvBtn');

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchDebounceTimeout);
      searchDebounceTimeout = setTimeout(() => {
        currentPage = 1;
        loadTransactions();
      }, 350);
    });
  }

  [typeFilter, categoryFilter, classificationFilter, sortFilter].forEach(el => {
    if (el) {
      el.addEventListener('change', () => {
        currentPage = 1;
        loadTransactions();
      });
    }
  });

  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      exportTransactionsCSV();
    });
  }
}

async function loadTransactions() {
  const search = document.getElementById('searchQuery')?.value.trim() || '';
  const type = document.getElementById('typeFilter')?.value || '';
  const category = document.getElementById('categoryFilter')?.value || '';
  const classification = document.getElementById('classificationFilter')?.value || '';
  const sort = document.getElementById('sortFilter')?.value || 'date_desc';

  let sortBy = 'date';
  let order = 'desc';
  if (sort === 'date_asc') { sortBy = 'date'; order = 'asc'; }
  else if (sort === 'amount_desc') { sortBy = 'amount'; order = 'desc'; }
  else if (sort === 'amount_asc') { sortBy = 'amount'; order = 'asc'; }

  let query = `/transactions?page=${currentPage}&limit=${PAGE_SIZE}&sort_by=${sortBy}&order=${order}`;
  if (search) query += `&search=${encodeURIComponent(search)}`;
  if (type && type !== 'all') query += `&transaction_type=${type}`;
  if (category && category !== 'all') query += `&category=${encodeURIComponent(category)}`;
  if (classification && classification !== 'all') query += `&need_or_want=${classification}`;

  try {
    const data = await apiRequest(query);
    renderTransactionsTable(data.items || []);
    renderPagination(data.total, data.page, data.total_pages);
    initIcons();
  } catch (err) {
    showToast('Failed to load transactions: ' + err.message, 'error');
  }
}

function renderTransactionsTable(items) {
  const tbody = document.getElementById('transactionsTableBody');
  if (!tbody) return;

  if (items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">
          <i data-lucide="inbox" class="empty-state-icon"></i>
          <div class="empty-state-title">No transactions match your query</div>
          <p class="empty-state-text">Try adjusting your filters or click "+ Add Transaction" to log an entry.</p>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = items.map(tx => `
    <tr>
      <td style="font-weight: 600; color: var(--text-main);">
        ${formatDate(tx.transaction_date)}
      </td>
      <td>
        <span class="badge ${tx.transaction_type === 'income' ? 'badge-success' : 'badge-danger'}">
          ${tx.transaction_type}
        </span>
      </td>
      <td>
        <span class="badge badge-primary">${tx.category}</span>
        ${tx.is_recurring ? '<span class="badge badge-warning" style="margin-left: 0.3rem;">Recurring</span>' : ''}
      </td>
      <td style="color: var(--text-main); font-weight: 500;">
        ${tx.description || '—'}
      </td>
      <td>
        <span class="badge badge-info">${tx.need_or_want}</span>
      </td>
      <td style="font-weight: 800; color: ${tx.transaction_type === 'income' ? 'var(--color-secondary)' : 'var(--text-main)'}; font-size: 0.95rem;">
        ${tx.transaction_type === 'income' ? '+' : '-'}${formatINR(tx.amount)}
      </td>
      <td style="text-align: right;">
        <button class="btn btn-outline btn-sm" onclick="openEditModal(${tx.id})" title="Edit" style="padding: 0.3rem 0.5rem; margin-right: 0.3rem;">
          <i data-lucide="edit-2" style="width: 14px; height: 14px;"></i>
        </button>
        <button class="btn btn-outline btn-sm" onclick="confirmDeleteTx(${tx.id})" title="Delete" style="padding: 0.3rem 0.5rem; color: var(--color-danger); border-color: rgba(244,63,94,0.3);">
          <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

function renderPagination(total, page, totalPages) {
  const infoEl = document.getElementById('paginationInfo');
  const prevBtn = document.getElementById('paginationPrev');
  const nextBtn = document.getElementById('paginationNext');

  if (infoEl) {
    infoEl.textContent = total > 0 
      ? `Showing page ${page} of ${totalPages} (${total} total records)`
      : 'No records';
  }

  if (prevBtn) {
    prevBtn.disabled = page <= 1;
    prevBtn.onclick = () => {
      if (currentPage > 1) {
        currentPage--;
        loadTransactions();
      }
    };
  }

  if (nextBtn) {
    nextBtn.disabled = page >= totalPages;
    nextBtn.onclick = () => {
      if (currentPage < totalPages) {
        currentPage++;
        loadTransactions();
      }
    };
  }
}

function setupAddEditModal() {
  const form = document.getElementById('transactionForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = Number(document.getElementById('txAmount').value);
    const type = document.getElementById('txType').value;
    const category = document.getElementById('txCategory').value;
    const desc = document.getElementById('txDesc').value;
    const dateVal = document.getElementById('txDate').value || new Date().toISOString().split('T')[0];
    const classification = document.getElementById('txClassification').value;
    const isRecurring = document.getElementById('txRecurring').checked;

    const payload = {
      amount,
      transaction_type: type,
      category,
      description: desc,
      transaction_date: dateVal,
      need_or_want: classification,
      is_recurring: isRecurring
    };

    try {
      if (currentEditingTxId) {
        await apiRequest(`/transactions/${currentEditingTxId}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
        showToast('Transaction updated successfully!', 'success');
      } else {
        await apiRequest('/transactions', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        showToast('Transaction created successfully!', 'success');
      }
      closeModal('transactionModal');
      currentEditingTxId = null;
      form.reset();
      await loadTransactions();
    } catch (err) {
      showToast('Error saving transaction: ' + err.message, 'error');
    }
  });
}

function openAddModal() {
  currentEditingTxId = null;
  const form = document.getElementById('transactionForm');
  if (form) form.reset();
  const title = document.getElementById('transactionModalTitle');
  if (title) title.textContent = 'Add Transaction';
  const dateInput = document.getElementById('txDate');
  if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];
  openModal('transactionModal');
}

async function openEditModal(txId) {
  try {
    const tx = await apiRequest(`/transactions/${txId}`);
    currentEditingTxId = tx.id;

    document.getElementById('transactionModalTitle').textContent = 'Edit Transaction';
    document.getElementById('txAmount').value = tx.amount;
    document.getElementById('txType').value = tx.transaction_type;
    document.getElementById('txCategory').value = tx.category;
    document.getElementById('txDesc').value = tx.description || '';
    document.getElementById('txDate').value = tx.transaction_date;
    document.getElementById('txClassification').value = tx.need_or_want;
    document.getElementById('txRecurring').checked = tx.is_recurring;

    openModal('transactionModal');
  } catch (err) {
    showToast('Failed to fetch transaction: ' + err.message, 'error');
  }
}

let pendingDeleteTxId = null;
function confirmDeleteTx(txId) {
  pendingDeleteTxId = txId;
  openModal('deleteConfirmModal');
}

function setupDeleteModal() {
  const btn = document.getElementById('confirmDeleteBtn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    if (!pendingDeleteTxId) return;
    try {
      await apiRequest(`/transactions/${pendingDeleteTxId}`, { method: 'DELETE' });
      showToast('Transaction deleted.', 'info');
      closeModal('deleteConfirmModal');
      pendingDeleteTxId = null;
      await loadTransactions();
    } catch (err) {
      showToast('Failed to delete transaction: ' + err.message, 'error');
    }
  });
}

function exportTransactionsCSV() {
  const token = getToken();
  const url = `${API_BASE}/transactions/export/csv`;
  
  // Create an anchor and fetch with auth header
  fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  .then(res => res.blob())
  .then(blob => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `pennypilot_transactions_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Transactions CSV exported!', 'success');
  })
  .catch(err => {
    showToast('Failed to export CSV: ' + err.message, 'error');
  });
}
