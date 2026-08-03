/* ============================================================
   student.js — Student Dashboard
   ============================================================ */

const StudentDashboard = (() => {
  let isLoaded = false;

  async function load() {
    if (isLoaded) return;
    renderSkeleton();

    try {
      // In a real app, we'd fetch data for the logged in user.
      // Here, we simulate it by picking the top contributor from the leaderboard.
      const lbData = await API.leaderboard('all_time');
      const board = lbData.leaderboard || [];
      const me = board.length > 0 ? board[0] : null;
      
      renderStats(me);

      if (me) {
        // Fetch real contributions for this user
        const activity = await API.contributions(me.username || me.github_username);
        renderActivity(activity.contributions || []);
      } else {
        renderActivity([]);
      }

      isLoaded = true;
    } catch (err) {
      console.error('Failed to load student dashboard:', err);
      showToast('Failed to load student dashboard', 'error');
    }
  }

  function renderSkeleton() {
    const statsGrid = document.getElementById('student-stats');
    if (statsGrid) {
      statsGrid.innerHTML = `
        <div class="stat-card"><div class="stat-label">My Score</div><div class="skeleton" style="width:60px;margin-top:8px;"></div></div>
        <div class="stat-card"><div class="stat-label">Merged PRs</div><div class="skeleton" style="width:50px;margin-top:8px;"></div></div>
        <div class="stat-card"><div class="stat-label">Issues Closed</div><div class="skeleton" style="width:50px;margin-top:8px;"></div></div>
        <div class="stat-card"><div class="stat-label">Rank</div><div class="skeleton" style="width:50px;margin-top:8px;"></div></div>
      `;
    }
    const activity = document.getElementById('student-activity');
    if (activity) {
      activity.innerHTML = `<div class="skeleton-row"><div class="skeleton-circle" style="width:8px;height:8px;margin-top:6px;"></div><div class="skeleton-text"><div class="skeleton" style="width:200px;"></div></div></div>`;
    }
  }

  function renderStats(me) {
    const statsGrid = document.getElementById('student-stats');
    if (!statsGrid) return;
    
    if (!me) {
      statsGrid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1;">No data available.</div>`;
      return;
    }

    statsGrid.innerHTML = `
      <div class="stat-card">
        <div class="stat-label">My Score</div>
        <div class="stat-val">${(me.total_score || 0).toLocaleString()}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Merged PRs</div>
        <div class="stat-val">${me.merged_prs || 0}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Issues Closed</div>
        <div class="stat-val">${me.issues_closed || 0}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Global Rank</div>
        <div class="stat-val">#1 (Simulated)</div>
      </div>
    `;
  }

  function renderActivity(events) {
    const container = document.getElementById('student-activity');
    if (!container) return;

    if (!events || events.length === 0) {
      container.innerHTML = '<div class="empty-state" style="padding:24px;">No recent activity found.</div>';
      return;
    }

    const html = events.slice(0, 5).map(e => `
      <div style="display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--border);">
        <div style="color:var(--c-sage);">
          ${e.event_type === 'pull_request' ? '🔄' : '💬'}
        </div>
        <div>
          <div style="font-size:var(--fs-sm);color:var(--t-primary);">
            You ${e.event_type === 'pull_request' ? 'merged a PR' : 'closed an issue'} in <strong>${escHtml(e.repo_name)}</strong>
          </div>
          <div style="font-size:var(--fs-xs);color:var(--t-muted);margin-top:4px;">
            ${relativeTime(e.timestamp)}
          </div>
        </div>
      </div>
    `).join('');
    container.innerHTML = html;
  }

  return { load };
})();

// Register
Router.register('student', StudentDashboard.load);
