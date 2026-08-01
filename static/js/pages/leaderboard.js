/**
 * Leaderboards Page
 */

async function renderLeaderboards() {
  const container = document.getElementById('leaderboards-content');
  
  // Skeleton
  container.innerHTML = `
    <div class="card">
      <div class="skeleton-text" style="width: 200px; margin-bottom: 24px;"></div>
      ${Array(5).fill('<div class="skeleton-row" style="margin-bottom: 12px;"><div class="skeleton-box" style="height:40px;"></div></div>').join('')}
    </div>
  `;

  try {
    const data = await apiFetch("/api/leaderboard?period=all_time");
    const users = data.leaderboard || [];

    const headers = ['Rank', 'Contributor', 'PRs', 'Issues', 'Reviews', 'Score'];
    
    const rows = users.map((u, i) => {
      const rankHtml = i < 3 
        ? `<span style="display: inline-flex; width: 24px; height: 24px; align-items: center; justify-content: center; border-radius: 50%; background: ${i === 0 ? '#FEF08A' : i === 1 ? '#E5E7EB' : '#FED7AA'}; color: #000; font-weight: 600; font-size: 12px;">${i+1}</span>`
        : `<span style="font-weight: 500; color: var(--text-muted); padding-left: 8px;">${i+1}</span>`;

      const userHtml = `
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="avatar-small" style="font-size: 12px; font-weight:600; background: var(--color-light-gray); color: var(--text-secondary);">${(u.name || u.username).substring(0,2).toUpperCase()}</div>
          <div>
            <div style="font-weight: 500; font-size: 14px; color: var(--text-primary);">${u.name || u.username}</div>
            <div style="font-size: 12px; color: var(--text-muted);">@${u.username}</div>
          </div>
        </div>
      `;

      return [
        rankHtml,
        userHtml,
        u.score?.merged_prs || 0,
        u.score?.issues_closed || 0,
        u.score?.reviews || 0,
        `<span style="font-weight: 600; color: var(--color-forest);">${u.score?.total || 0}</span>`
      ];
    });

    const tableHtml = createTable(headers, rows);

    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <div style="display: flex; gap: 8px;">
           <button class="btn btn-secondary" style="background: var(--color-forest); color: white; border-color: var(--color-forest);">Global</button>
           <button class="btn btn-secondary">Department</button>
           <button class="btn btn-secondary">Freshers</button>
        </div>
        <select class="global-search" style="width: 150px;">
          <option>All Time</option>
          <option>This Month</option>
          <option>This Week</option>
        </select>
      </div>
      <div class="card">
        ${tableHtml}
      </div>
    `;

  } catch (err) {
    container.innerHTML = `<div class="card"><p style="color: var(--color-danger)">Failed to load leaderboards: ${err.message}</p></div>`;
  }
}
