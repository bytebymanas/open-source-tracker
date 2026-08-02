/* ============================================================
   goals.js — Contribution milestones with progress bars
   ============================================================ */
const PLATFORM_GOALS = [
  {
    id: 'first_pr',     name: 'First Pull Request',
    desc: 'Any contributor merges their first PR',
    target: 1,  metric: 'pr_count',    category: 'Contributions',
  },
  {
    id: 'ten_prs',      name: '10 Merged PRs',
    desc: 'Platform total reaches 10 merged pull requests',
    target: 10, metric: 'pr_count',    category: 'Contributions',
  },
  {
    id: 'fifty_prs',    name: '50 Merged PRs',
    desc: 'Platform total reaches 50 merged pull requests',
    target: 50, metric: 'pr_count',    category: 'Contributions',
  },
  {
    id: 'five_issues',  name: '5 Issues Closed',
    desc: 'Platform total reaches 5 closed issues',
    target: 5,  metric: 'issue_count', category: 'Contributions',
  },
  {
    id: 'score_50',     name: 'Top Score 50',
    desc: 'Any contributor reaches a score of 50',
    target: 50, metric: 'top_score',   category: 'Scores',
  },
  {
    id: 'score_100',    name: 'Top Score 100',
    desc: 'Any contributor reaches a score of 100',
    target: 100,metric: 'top_score',   category: 'Scores',
  },
  {
    id: 'contributors_5', name: '5 Contributors',
    desc: 'Platform has at least 5 tracked contributors',
    target: 5,  metric: 'total_contributors', category: 'Growth',
  },
  {
    id: 'contributors_20', name: '20 Contributors',
    desc: 'Platform has at least 20 tracked contributors',
    target: 20, metric: 'total_contributors', category: 'Growth',
  },
];

async function renderGoals() {
  const list = document.getElementById('goals-list');
  list.innerHTML = `
    <div class="skeleton" style="height:80px;border-radius:12px;"></div>
    <div class="skeleton" style="height:80px;border-radius:12px;margin-top:12px;"></div>`;

  try {
    const [stuData, lbData] = await Promise.all([
      State.cache('students', () => API.students()),
      State.cache('lb-all_time', () => API.leaderboard('all_time')),
    ]);

    const students = stuData.students || [];
    const board    = lbData.leaderboard || [];
    const totals = {
      pr_count:            board.reduce((s, u) => s + (u.merged_prs || 0), 0),
      issue_count:         board.reduce((s, u) => s + (u.issues_closed || 0), 0),
      top_score:           board.length ? Math.max(...board.map(u => u.total_score || 0)) : 0,
      total_contributors:  students.length,
    };

    // Group by category
    const categories = [...new Set(PLATFORM_GOALS.map(g => g.category))];

    list.innerHTML = categories.map(cat => {
      const goalsInCat = PLATFORM_GOALS.filter(g => g.category === cat);
      const cards = goalsInCat.map(g => {
        const current = totals[g.metric] || 0;
        const pct     = Math.min(100, Math.round((current / g.target) * 100));
        const done    = pct >= 100;
        return `
          <div class="goal-card ${done ? 'done' : ''}">
            <div class="goal-info">
              <div class="goal-name">${done ? '✅ ' : ''}${escHtml(g.name)}</div>
              <div class="goal-desc">${escHtml(g.desc)}</div>
            </div>
            <div class="goal-progress">
              <div class="progress-bar-wrap">
                <div class="progress-bar-fill" style="width:${pct}%"></div>
              </div>
              <div class="goal-progress-label">${current} / ${g.target}</div>
            </div>
            <span class="badge ${done ? 'badge-success' : 'badge-neutral'}" style="min-width:44px;justify-content:center;">${pct}%</span>
          </div>`;
      }).join('');

      return `
        <div style="margin-bottom:24px;">
          <div class="sidebar-section-label" style="color:var(--t-muted);font-size:var(--fs-xs);font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;">${escHtml(cat)}</div>
          <div class="goals-list">${cards}</div>
        </div>`;
    }).join('');

  } catch (err) {
    list.innerHTML = `<div class="card">${errorState(err, 'renderGoals()')}</div>`;
  }
}
