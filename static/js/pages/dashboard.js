/* ============================================================
   dashboard.js
   ============================================================ */
async function renderDashboard() {
  try {
    const [stuData, lbData] = await Promise.all([
      State.cache('students', () => API.students()),
      State.cache('lb-all', () => API.leaderboard('all_time')),
    ]);

    const students = stuData.students || [];
    const board    = lbData.leaderboard || [];
    const totalPRs   = board.reduce((s, u) => s + (u.merged_prs || 0), 0);
    const totalIssues= board.reduce((s, u) => s + (u.issues_closed || 0), 0);
    const avgScore   = board.length ? Math.round(board.reduce((s, u) => s + (u.total_score || 0), 0) / board.length) : 0;

    // Stats
    document.getElementById('dashboard-stats').innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Contributors</div>
        <div class="stat-value">${students.length}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Merged PRs</div>
        <div class="stat-value">${totalPRs}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Issues Closed</div>
        <div class="stat-value">${totalIssues}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Avg Score</div>
        <div class="stat-value">${avgScore}</div>
      </div>`;

    // Top contributors
    if (!board.length) {
      document.getElementById('dashboard-top-list').innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 13h4v7H4zm6-7h4v14h-4zm6 4h4v10h-4z"/></svg></div>
          <h3>No contributors yet</h3>
          <p>Import contributors to see them here</p>
          <button class="btn btn-primary btn-sm" id="dash-add-btn">Import Contributors</button>
        </div>`;
      document.getElementById('dash-add-btn')?.addEventListener('click', () => {
        document.getElementById('add-usernames-input').value = '';
        document.getElementById('add-result').innerHTML = '';
        openModal('modal-add');
      });
    } else {
      const rows = board.slice(0, 8).map((u, i) => {
        const medal = ['🥇','🥈','🥉'][i] || `${i+1}`;
        const rankClass = ['top-1','top-2','top-3'][i] || '';
        return `<tr style="cursor:pointer;" data-profile="${escHtml(u.github_username)}">
          <td><span class="rank-num ${rankClass}">${medal}</span></td>
          <td>
            <div class="user-cell">
              <div class="avatar avatar-sm">${avatarInitials(u.name || u.github_username)}</div>
              <div class="user-cell-info">
                <div class="user-cell-name">${escHtml(u.name || u.github_username)}</div>
                <div class="user-cell-sub">@${escHtml(u.github_username)}</div>
              </div>
            </div>
          </td>
          <td><span class="score-display">${u.total_score || 0} pts</span></td>
        </tr>`;
      }).join('');

      document.getElementById('dashboard-top-list').innerHTML = `
        <div class="table-wrap">
          <table>
            <thead><tr><th>#</th><th>Contributor</th><th>Score</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;

      document.querySelectorAll('#dashboard-top-list tr[data-profile]').forEach(row => {
        row.addEventListener('click', () => {
          State.set('profileUsername', row.dataset.profile);
          Router.navigate('profile');
        });
      });
    }

    // Recent activity panel
    const activityItems = board.slice(0, 6).map(u => `
      <div class="activity-item" style="border-radius:0;padding:12px 20px;">
        <div class="activity-dot ${(u.merged_prs || 0) > 0 ? 'pr' : 'issue'}"></div>
        <div class="activity-content">
          <strong>${escHtml(u.name || u.github_username)}</strong>
          — ${u.merged_prs || 0} PR${u.merged_prs !== 1 ? 's' : ''}, ${u.issues_closed || 0} issue${u.issues_closed !== 1 ? 's' : ''}
          <div class="activity-meta">Score: ${u.total_score || 0} pts</div>
        </div>
      </div>`).join('');

    document.getElementById('dashboard-activity').innerHTML =
      activityItems || `<div class="empty-state" style="padding:24px;"><h3>No activity</h3></div>`;

  } catch (err) {
    document.getElementById('dashboard-stats').innerHTML =
      `<div class="stat-card"><div class="error-state"><p>${escHtml(err.message)}</p><button class="btn btn-secondary btn-sm mt-4" onclick="renderDashboard()">Retry</button></div></div>`;
  }
}
