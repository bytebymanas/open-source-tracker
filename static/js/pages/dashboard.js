/**
 * Dashboard Page
 */

async function renderDashboard() {
  const container = document.getElementById('dashboard-content');
  
  // Initial Skeleton State
  container.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 24px; margin-bottom: 32px;">
      ${Array(5).fill('<div class="card"><div class="skeleton-text"></div><div class="skeleton-box" style="height:40px;"></div></div>').join('')}
    </div>
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px;">
      <div class="card"><div class="skeleton-box" style="height:300px;"></div></div>
      <div class="card"><div class="skeleton-box" style="height:300px;"></div></div>
    </div>
  `;

  try {
    const data = await apiFetch("/api/leaderboard?period=all_time");
    const users = data.leaderboard || [];

    // Calculate aggregates
    const totalContributors = users.length;
    let totalPRs = 0;
    let totalIssues = 0;
    let totalReviews = 0;
    let topScore = 0;

    users.forEach(u => {
      totalPRs += (u.score?.merged_prs || 0);
      totalIssues += (u.score?.issues_closed || 0);
      totalReviews += (u.score?.reviews || 0);
      if ((u.score?.total || 0) > topScore) topScore = u.score.total;
    });

    // We don't have a backend endpoint for total repositories across the org, so we estimate or use a placeholder
    const totalRepos = 12; 

    // Render Stats Row
    const statsHtml = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 24px; margin-bottom: 32px;">
        ${createStatCard('Contributors', totalContributors)}
        ${createStatCard('Merged PRs', totalPRs)}
        ${createStatCard('Closed Issues', totalIssues)}
        ${createStatCard('Reviews', totalReviews)}
        ${createStatCard('Repositories', totalRepos)}
      </div>
    `;

    // Render Top Contributors
    const topUsers = users.slice(0, 5);
    const topContributorsHtml = `
      <div class="card" style="margin-bottom: 24px;">
        <h3 style="margin-top:0; font-size: 16px; color: var(--text-secondary);">Top Contributors</h3>
        <div style="display: flex; flex-direction: column; gap: 16px; margin-top: 16px;">
          ${topUsers.map((u, i) => `
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <div style="display: flex; align-items: center; gap: 12px;">
                <div class="avatar-small" style="font-size: 12px; font-weight:600; background: var(--color-mint); color: var(--color-forest);">#${i+1}</div>
                <div>
                  <div style="font-weight: 500; font-size: 14px;">${u.name || u.username}</div>
                  <div style="font-size: 12px; color: var(--text-muted);">@${u.username}</div>
                </div>
              </div>
              <div style="font-weight: 600; font-size: 14px; color: var(--color-forest);">${u.score?.total || 0} pts</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Render Recent Activity (Mocked for now as backend doesn't have a global feed endpoint)
    const activityHtml = `
      <div class="card" style="margin-bottom: 24px;">
        <h3 style="margin-top:0; font-size: 16px; color: var(--text-secondary);">Recent Activity</h3>
        <div style="display: flex; flex-direction: column; gap: 16px; margin-top: 16px;">
          <div style="display: flex; gap: 12px; align-items: flex-start;">
            <div class="badge badge-success" style="padding: 4px 8px;">PR</div>
            <div>
              <div style="font-size: 14px;"><strong>Manas Chhabra</strong> merged a PR in <code>frontend-core</code></div>
              <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">2 hours ago</div>
            </div>
          </div>
          <div style="display: flex; gap: 12px; align-items: flex-start;">
            <div class="badge" style="background: var(--color-warning-light); color: var(--color-warning); padding: 4px 8px;">Issue</div>
            <div>
              <div style="font-size: 14px;"><strong>Ayushi Mishra</strong> closed an issue in <code>api-service</code></div>
              <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">5 hours ago</div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Assemble Page
    container.innerHTML = `
      ${statsHtml}
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px;">
        <div>
           <div class="card" style="margin-bottom: 24px;">
             <h3 style="margin-top:0; font-size: 16px; color: var(--text-secondary);">Contribution Overview</h3>
             <div style="height: 250px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); background: var(--color-light-gray); border-radius: 8px; margin-top: 16px;">
                Chart area (Chart.js integration pending)
             </div>
           </div>
        </div>
        <div>
          ${topContributorsHtml}
          ${activityHtml}
        </div>
      </div>
    `;

  } catch (err) {
    container.innerHTML = `<div class="card"><p style="color: var(--color-danger)">Failed to load dashboard: ${err.message}</p></div>`;
  }
}
