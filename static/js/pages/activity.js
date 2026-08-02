/* ============================================================
   activity.js — Grouped activity timeline (per spec)
   ============================================================ */
async function renderActivity() {
  const container = document.getElementById('activity-content');
  const filter    = document.getElementById('activity-filter')?.value || '';

  container.innerHTML = `
    <div class="skeleton-row"><div class="skeleton-circle" style="width:8px;height:8px;margin-top:6px;flex-shrink:0;"></div>
    <div class="skeleton-text"><div class="skeleton" style="width:320px;"></div></div></div>`.repeat(5);

  try {
    const data = await State.cache('students', () => API.students());
    const students = data.students || [];

    if (!students.length) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 2.05v2.02c3.95.49 7 3.85 7 7.93 0 3.21-1.81 6-4.5 7.54L13 17v5h5l-1.22-1.22C19.91 19.07 22 15.76 22 12c0-5.18-3.95-9.45-9-9.95zM11 2.05C5.95 2.55 2 6.82 2 12c0 3.76 2.09 7.07 5.22 8.78L6 22h5V2.05z"/></svg></div>
          <h3>No activity yet</h3>
          <p>Import contributors to see their contribution activity here</p>
          <button class="btn btn-primary btn-sm mt-4" id="act-add-btn">Import Contributors</button>
        </div>`;
      document.getElementById('act-add-btn')?.addEventListener('click', () => {
        openModal('modal-add');
      });
      return;
    }

    // Sort by score descending, group by today/yesterday/this-week/earlier
    const sorted = [...students].sort((a, b) => (b.total_score || 0) - (a.total_score || 0));

    // Apply type filter if set
    // Build items — each student becomes an activity item
    const buildItems = (list) => list.map(s => {
      const hasPR    = (s.pr_count || 0) > 0;
      const hasIssue = (s.issue_count || 0) > 0;
      const dotClass = hasPR ? 'pr' : hasIssue ? 'issue' : '';

      return `
        <div class="activity-item">
          <div class="activity-dot ${dotClass}"></div>
          <div class="activity-content">
            <strong>
              <button class="btn-ghost btn-sm" style="padding:0;font-weight:500;cursor:pointer;"
                data-profile="${escHtml(s.github_username)}">${escHtml(s.name || s.github_username)}</button>
            </strong>
            — ${s.pr_count || 0} merged PR${s.pr_count !== 1 ? 's' : ''}, ${s.issue_count || 0} closed issue${s.issue_count !== 1 ? 's' : ''}
            ${s.department ? `<span class="text-muted"> · ${escHtml(s.department)}</span>` : ''}
            <div class="activity-meta">Score: <strong class="text-accent">${s.total_score || 0} pts</strong></div>
          </div>
          <div>
            <button class="btn btn-secondary btn-sm" data-profile="${escHtml(s.github_username)}">View →</button>
          </div>
        </div>`;
    }).join('');

    // Group: top contributors, rest
    const topN = 5;
    const top  = sorted.slice(0, topN);
    const rest = sorted.slice(topN);

    let html = '';

    html += `<div class="activity-group">
      <div class="activity-group-label">Top Contributors</div>
      <div class="card">${buildItems(top)}</div>
    </div>`;

    if (rest.length) {
      html += `<div class="activity-group">
        <div class="activity-group-label">All Contributors</div>
        <div class="card">${buildItems(rest)}</div>
      </div>`;
    }

    container.innerHTML = html;

    container.querySelectorAll('[data-profile]').forEach(el => {
      el.addEventListener('click', () => {
        State.set('profileUsername', el.dataset.profile);
        Router.navigate('profile');
      });
    });

  } catch (err) {
    container.innerHTML = `<div class="card">${errorState(err, 'renderActivity()')}</div>`;
  }
}

// Filter listener
document.getElementById('activity-filter')?.addEventListener('change', renderActivity);
