/* ============================================================
   org.js — Organization Dashboard
   ============================================================ */

const OrgDashboard = (() => {
  let isLoaded = false;

  async function load() {
    if (isLoaded) return;
    renderSkeleton();

    try {
      const [stuData, lbData] = await Promise.all([
        State.cache('students', () => API.students()),
        State.cache('lb-all', () => API.leaderboard('all_time')),
      ]);

      const students = stuData.students || [];
      const board = lbData.leaderboard || [];

      renderStats(students, board);
      renderTopContributors(board);
      renderDepartments(board);

      isLoaded = true;
    } catch (err) {
      console.error('Failed to load org dashboard:', err);
      showToast('Failed to load organization data', 'error');
    }
  }

  function renderSkeleton() {
    const statsGrid = document.getElementById('org-stats');
    if (statsGrid) {
      statsGrid.innerHTML = `
        <div class="stat-card"><div class="stat-label">Total Departments</div><div class="skeleton" style="width:60px;margin-top:8px;"></div></div>
        <div class="stat-card"><div class="stat-label">Active Contributors</div><div class="skeleton" style="width:50px;margin-top:8px;"></div></div>
        <div class="stat-card"><div class="stat-label">Total PRs Merged</div><div class="skeleton" style="width:50px;margin-top:8px;"></div></div>
        <div class="stat-card"><div class="stat-label">Avg Dept Score</div><div class="skeleton" style="width:50px;margin-top:8px;"></div></div>
      `;
    }
    const depts = document.getElementById('org-departments');
    if (depts) depts.innerHTML = `<div class="skeleton-row"><div class="skeleton-text"><div class="skeleton" style="width:100%;"></div></div></div>`;
    
    const top = document.getElementById('org-top-contributors');
    if (top) top.innerHTML = `<div class="skeleton-row"><div class="skeleton-text"><div class="skeleton" style="width:100%;"></div></div></div>`;
  }

  function renderStats(students, board) {
    const statsGrid = document.getElementById('org-stats');
    if (!statsGrid) return;
    
    const totalPRs = board.reduce((s, u) => s + (u.merged_prs || 0), 0);
    const avgScore = board.length ? Math.round(board.reduce((s, u) => s + (u.total_score || 0), 0) / board.length) : 0;
    
    const depts = new Set(board.map(c => c.department).filter(Boolean));

    statsGrid.innerHTML = `
      <div class="stat-card"><div class="stat-label">Total Departments</div><div class="stat-val">${depts.size || 0}</div></div>
      <div class="stat-card"><div class="stat-label">Active Contributors</div><div class="stat-val">${students.length}</div></div>
      <div class="stat-card"><div class="stat-label">Total PRs Merged</div><div class="stat-val">${totalPRs}</div></div>
      <div class="stat-card"><div class="stat-label">Avg Contributor Score</div><div class="stat-val">${avgScore}</div></div>
    `;
  }

  function renderDepartments(lb) {
    const container = document.getElementById('org-departments');
    if (!container) return;

    // Group by department
    const depts = {};
    lb.forEach(c => {
      const d = c.department || 'Unknown';
      if (!depts[d]) depts[d] = { count: 0, score: 0 };
      depts[d].count++;
      depts[d].score += (c.total_score || 0);
    });

    const sorted = Object.keys(depts).map(k => ({ name: k, ...depts[k] })).sort((a,b) => b.score - a.score);

    if (sorted.length === 0) {
      container.innerHTML = '<div class="empty-state">No department data available.</div>';
      return;
    }

    const html = sorted.map((d, i) => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border);">
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="font-weight:600;color:var(--t-muted);width:20px;">#${i+1}</div>
          <div>
            <div style="font-weight:500;">${escHtml(d.name)}</div>
            <div style="font-size:var(--fs-xs);color:var(--t-secondary);">${d.count} contributors</div>
          </div>
        </div>
        <div style="font-weight:600;">
          ${d.score.toLocaleString()} pts
        </div>
      </div>
    `).join('');
    container.innerHTML = html;
  }

  function renderTopContributors(lb) {
    const container = document.getElementById('org-top-contributors');
    if (!container) return;

    const top = lb.slice(0, 10);
    if (top.length === 0) {
      container.innerHTML = '<div class="empty-state">No contributors found.</div>';
      return;
    }

    const html = top.map(c => {
      const uname = c.username || c.github_username;
      return `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border);">
        <div style="display:flex;align-items:center;gap:12px;">
          <div class="avatar" style="width:32px;height:32px;font-size:12px;">${uname.substring(0,2).toUpperCase()}</div>
          <div>
            <div style="font-weight:500;">${escHtml(uname)}</div>
            <div style="font-size:var(--fs-xs);color:var(--t-secondary);">${escHtml(c.department || 'No dept')}</div>
          </div>
        </div>
        <div style="font-weight:600;color:var(--c-forest);">
          ${(c.total_score || 0).toLocaleString()} pts
        </div>
      </div>
    `).join('');
    container.innerHTML = html;
  }

  return { load };
})();

// Register
Router.register('org', OrgDashboard.load);
