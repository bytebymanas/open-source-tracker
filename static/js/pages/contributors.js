/* ============================================================
   contributors.js
   ============================================================ */
let _allStudents = [];
let _pendingDeleteUser = null;

async function renderContributors() {
  setupContributorListeners();
  await loadContributors();
}

function setupContributorListeners() {
  // Search (debounced)
  const searchEl = document.getElementById('contributors-search');
  if (searchEl && !searchEl._bound) {
    searchEl._bound = true;
    searchEl.addEventListener('input', debounce(() => renderContributorsTable(), 250));
  }

  // Department filter
  const deptEl = document.getElementById('contributors-dept-filter');
  if (deptEl && !deptEl._bound) {
    deptEl._bound = true;
    deptEl.addEventListener('change', renderContributorsTable);
  }

  // Open add modal
  document.getElementById('open-add-modal')?.addEventListener('click', () => {
    document.getElementById('add-usernames-input').value = '';
    document.getElementById('add-result').innerHTML = '';
    openModal('modal-add');
  });
}

async function loadContributors() {
  document.getElementById('contributors-tbody').innerHTML = skeletonRows(5, 6);
  try {
    const data = await API.students();
    _allStudents = data.students || [];
    State.set('allStudents', _allStudents);
    renderContributorsTable();
  } catch (err) {
    document.getElementById('contributors-tbody').innerHTML =
      `<tr><td colspan="6">${errorState(err, 'loadContributors()')}</td></tr>`;
  }
}

function renderContributorsTable() {
  const q    = (document.getElementById('contributors-search')?.value || '').toLowerCase();
  const dept = document.getElementById('contributors-dept-filter')?.value || '';

  const filtered = _allStudents.filter(s => {
    const matchQ    = !q || (s.github_username||'').toLowerCase().includes(q) || (s.name||'').toLowerCase().includes(q);
    const matchDept = !dept || (s.department||'') === dept;
    return matchQ && matchDept;
  });

  const tbody = document.getElementById('contributors-tbody');

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="6">
      <div class="empty-state" style="padding:32px;">
        <div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></div>
        <h3>${q || dept ? 'No results found' : 'No contributors yet'}</h3>
        <p>${q || dept ? 'Try adjusting your filters' : 'Import GitHub usernames to get started'}</p>
        ${!q && !dept ? `<button class="btn btn-primary btn-sm mt-4" id="ctb-add-empty">Import Contributors</button>` : ''}
      </div>
    </td></tr>`;
    document.getElementById('ctb-add-empty')?.addEventListener('click', () => {
      document.getElementById('add-usernames-input').value = '';
      document.getElementById('add-result').innerHTML = '';
      openModal('modal-add');
    });
    return;
  }

  tbody.innerHTML = filtered.map(s => `
    <tr>
      <td>
        <div class="user-cell">
          <div class="avatar avatar-sm">
            ${s.avatar_url ? `<img src="${escHtml(s.avatar_url)}" alt="${escHtml(s.github_username)}" loading="lazy"/>` : avatarInitials(s.name || s.github_username)}
          </div>
          <div class="user-cell-info">
            <div class="user-cell-name">
              <button class="btn-ghost btn-sm" style="padding:0;font-weight:500;" data-profile="${escHtml(s.github_username)}">${escHtml(s.name || s.github_username)}</button>
            </div>
            <div class="user-cell-sub">@${escHtml(s.github_username)}</div>
          </div>
        </div>
      </td>
      <td><span class="text-muted">${escHtml(s.department || '—')}</span></td>
      <td>${s.pr_count || 0}</td>
      <td>${s.issue_count || 0}</td>
      <td><span class="score-display">${s.total_score || 0} pts</span></td>
      <td>
        <div class="flex gap-2">
          <button class="btn btn-secondary btn-sm" data-edit="${escHtml(s.github_username)}"
            data-dept="${escHtml(s.department||'')}" data-uni="${escHtml(s.university||'')}">Edit</button>
          <button class="btn btn-danger btn-sm" data-delete="${escHtml(s.github_username)}">Delete</button>
        </div>
      </td>
    </tr>`).join('');

  // Profile links
  tbody.querySelectorAll('[data-profile]').forEach(btn => {
    btn.addEventListener('click', () => {
      State.set('profileUsername', btn.dataset.profile);
      Router.navigate('profile');
    });
  });

  // Edit
  tbody.querySelectorAll('[data-edit]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('edit-username').value    = btn.dataset.edit;
      document.getElementById('edit-dept').value        = btn.dataset.dept;
      document.getElementById('edit-university').value  = btn.dataset.uni;
      document.getElementById('modal-edit-title').textContent = `Edit @${btn.dataset.edit}`;
      openModal('modal-edit');
    });
  });

  // Delete (two-step confirm)
  tbody.querySelectorAll('[data-delete]').forEach(btn => {
    btn.addEventListener('click', () => {
      _pendingDeleteUser = btn.dataset.delete;
      document.getElementById('delete-username-label').textContent = `@${_pendingDeleteUser}`;
      openModal('modal-delete');
    });
  });
}

/* ---- Add modal ---- */
document.getElementById('confirm-add-btn')?.addEventListener('click', async () => {
  const raw   = document.getElementById('add-usernames-input').value;
  const users = raw.split(/[\n,]+/).map(u => u.trim().replace(/^@/,'')).filter(Boolean);
  if (!users.length) return;

  const btn = document.getElementById('confirm-add-btn');
  btn.disabled = true;
  btn.textContent = 'Importing…';
  document.getElementById('add-result').innerHTML = '';

  try {
    const data = await API.importStudents(users);
    const results = (data.results || []).map(r =>
      `<div style="font-size:var(--fs-sm);padding:3px 0;">
        ${r.status === 'ok'
          ? `<span class="badge badge-success">✓ @${escHtml(r.username)}</span>`
          : `<span class="badge badge-danger">✗ @${escHtml(r.username)}: ${escHtml(r.message||'failed')}</span>`
        }
      </div>`).join('');
    document.getElementById('add-result').innerHTML = `<div style="margin-top:12px;">${results}</div>`;
    if (data.imported > 0) {
      showToast(`Imported ${data.imported} contributor${data.imported !== 1 ? 's' : ''}`);
      State.invalidate('students');
      State.invalidate('lb-all_time');
      await loadContributors();
    }
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Import';
  }
});

/* ---- Edit modal ---- */
document.getElementById('confirm-edit-btn')?.addEventListener('click', async () => {
  const username = document.getElementById('edit-username').value;
  const dept     = document.getElementById('edit-dept').value.trim();
  const uni      = document.getElementById('edit-university').value.trim();

  try {
    await API.updateStudent(username, { department: dept || null, university: uni || null });
    showToast('Contributor updated');
    closeModal('modal-edit');
    State.invalidate('students');
    await loadContributors();
  } catch (err) {
    showToast(err.message, 'error');
  }
});

/* ---- Delete modal ---- */
document.getElementById('confirm-delete-btn')?.addEventListener('click', async () => {
  if (!_pendingDeleteUser) return;
  try {
    await API.deleteStudent(_pendingDeleteUser);
    showToast(`Removed @${_pendingDeleteUser}`);
    closeModal('modal-delete');
    _pendingDeleteUser = null;
    State.invalidate('students');
    State.invalidate('lb-all_time');
    await loadContributors();
  } catch (err) {
    showToast(err.message, 'error');
  }
});
