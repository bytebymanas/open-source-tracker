/* ============================================================
   leaderboard.js — /js/pages/leaderboard.js
   ============================================================ */
let _lbData  = [];
const _lb    = { period: 'all_time', dept: '', search: '' };
let _lbListenersInit = false;

async function renderLeaderboards() {
  // Populate department filter once
  if (!State.get('departments').length) {
    try {
      const d     = await API.departments();
      const depts = d.departments || [];
      State.set('departments', depts);
      ['lb-dept', 'contributors-dept-filter'].forEach(id => {
        const sel = document.getElementById(id);
        if (sel && depts.length) {
          sel.innerHTML = `<option value="">All Departments</option>` +
            depts.map(dep => `<option value="${escHtml(dep)}">${escHtml(dep)}</option>`).join('');
        }
      });
    } catch (_) {}
  }

  if (!_lbListenersInit) {
    _lbListenersInit = true;
    _initLbListeners();
  }

  await _loadLeaderboard();
}

function _initLbListeners() {
  // Period tabs
  document.querySelectorAll('[data-period]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-period]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _lb.period = btn.dataset.period;
      _lb.search = '';
      const searchEl = document.getElementById('lb-search');
      if (searchEl) searchEl.value = '';
      _loadLeaderboard();
    });
  });

  // Department filter
  document.getElementById('lb-dept')?.addEventListener('change', (e) => {
    _lb.dept = e.target.value;
    _renderLbTable();
  });

  // Search (debounced per spec)
  const searchEl = document.getElementById('lb-search');
  if (searchEl) {
    searchEl.addEventListener('input', debounce(() => {
      _lb.search = searchEl.value.toLowerCase().trim();
      _renderLbTable();
    }, 250));
  }

  // CSV export
  document.getElementById('lb-export-btn')?.addEventListener('click', () => {
    const url = `/api/leaderboard/export?period=${_lb.period}&format=csv` +
                (_lb.dept ? '&department=' + encodeURIComponent(_lb.dept) : '');
    window.open(url, '_blank');
  });
}

async function _loadLeaderboard() {
  const tbody = document.getElementById('lb-tbody');
  if (!tbody) return;
  tbody.innerHTML = _skeletonTbodyRows(6, 6);

  try {
    const cacheKey = `lb-${_lb.period}`;
    const data     = await State.cache(cacheKey, () => API.leaderboard(_lb.period, ''));
    _lbData = data.leaderboard || [];
    _renderLbTable();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6">${_errorHtml(err, '_loadLeaderboard()')}</td></tr>`;
  }
}

function _renderLbTable() {
  const tbody = document.getElementById('lb-tbody');
  if (!tbody) return;

  const q    = _lb.search;
  const dept = _lb.dept;

  const filtered = _lbData.filter(u => {
    const matchQ    = !q || (u.github_username||'').toLowerCase().includes(q) || (u.name||'').toLowerCase().includes(q);
    const matchDept = !dept || (u.department||'') === dept;
    return matchQ && matchDept;
  });

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="6">
      <div class="empty-state" style="padding:32px;">
        <div class="empty-state-icon">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 13h4v7H4zm6-7h4v14h-4zm6 4h4v10h-4z"/></svg>
        </div>
        <h3>${q || dept ? 'No results found' : 'No contributors yet'}</h3>
        <p>${q || dept ? 'Try adjusting your filters' : 'Import GitHub usernames to get started'}</p>
      </div>
    </td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map((u) => {
    const realRank  = _lbData.indexOf(u) + 1;
    const medal     = ['🥇', '🥈', '🥉'][realRank - 1] || realRank;
    const rankClass = ['top-1', 'top-2', 'top-3'][realRank - 1] || '';
    const uname = u.username || u.github_username;
    return `
      <tr style="cursor:pointer;" data-profile="${escHtml(uname)}">
        <td><span class="rank-num ${rankClass}">${medal}</span></td>
        <td>
          <div class="user-cell">
            <div class="avatar avatar-sm">${avatarInitials(u.name || uname)}</div>
            <div class="user-cell-info">
              <div class="user-cell-name">${escHtml(u.name || uname)}</div>
              <div class="user-cell-sub">@${escHtml(uname)}</div>
            </div>
          </div>
        </td>
        <td><span class="text-muted">${escHtml(u.department || '—')}</span></td>
        <td>${u.merged_prs || 0}</td>
        <td>${u.issues_closed || 0}</td>
        <td><span class="score-display">${u.total_score || 0} pts</span></td>
      </tr>`;
  }).join('');

  // Row click → profile
  tbody.querySelectorAll('tr[data-profile]').forEach(row => {
    row.addEventListener('click', () => {
      State.set('profileUsername', row.dataset.profile);
      Router.navigate('profile');
    });
  });
}

/* ---- Helpers shared with other page modules ---- */
function _skeletonTbodyRows(rows, cols) {
  return Array.from({ length: rows }, () =>
    `<tr>${Array.from({ length: cols }, () =>
      `<td><div class="skeleton" style="height:13px;"></div></td>`
    ).join('')}</tr>`
  ).join('');
}

function _errorHtml(err, retryCall) {
  return `
    <div class="error-state">
      <div class="error-state-icon">⚠</div>
      <h3>Something went wrong</h3>
      <p>${escHtml(err.message || 'Unknown error')}</p>
      <button class="btn btn-secondary btn-sm mt-4" onclick="${retryCall}">Retry</button>
    </div>`;
}

/* re-export as module-level names used by other pages */
function skeletonRows(rows, cols) { return _skeletonTbodyRows(rows, cols); }
function errorState(err, fn)       { return _errorHtml(err, fn); }
