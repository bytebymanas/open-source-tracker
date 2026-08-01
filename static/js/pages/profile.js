/**
 * Profile Page
 */

async function renderProfile() {
  const container = document.getElementById('profile-content');
  
  // Basic search/select state if no user selected
  container.innerHTML = `
    <div style="display: flex; gap: 12px; margin-bottom: 32px;">
      <input type="text" id="profile-search-input" class="global-search" placeholder="Enter GitHub username..." style="max-width: 300px;" />
      <button class="btn btn-primary" id="profile-search-btn">Search</button>
    </div>
    <div id="profile-details-container">
      <div class="card" style="text-align: center; color: var(--text-muted); padding: 48px;">
        Search for a user to view their profile.
      </div>
    </div>
  `;

  document.getElementById('profile-search-btn').addEventListener('click', async () => {
    const username = document.getElementById('profile-search-input').value.trim();
    if (!username) return;

    const detailsContainer = document.getElementById('profile-details-container');
    detailsContainer.innerHTML = `
      <div class="card">
        <div class="skeleton-box" style="height: 200px;"></div>
      </div>
    `;

    try {
      // Use existing endpoints: /api/students/<username>, /api/contributions/<username>
      // First get basic profile/score from leaderboard since there's no single student GET yet,
      // wait, the old API did have it via the leaderboard. 
      // Actually we have: GET /api/leaderboard and we filter by username.
      const lbData = await apiFetch("/api/leaderboard?period=all_time");
      const user = lbData.leaderboard?.find(u => u.username === username);

      if (!user) {
         detailsContainer.innerHTML = `<div class="card" style="color: var(--color-danger)">User not found in system.</div>`;
         return;
      }

      const contribs = await apiFetch(`/api/contributions/${username}`);

      // Render LinkedIn-style header
      const headerHtml = `
        <div class="card" style="margin-bottom: 24px; display: flex; gap: 24px; align-items: flex-start;">
          <div style="width: 120px; height: 120px; border-radius: 50%; background: var(--color-light-gray); display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 600; color: var(--text-secondary);">
            ${(user.name || user.username).substring(0,2).toUpperCase()}
          </div>
          <div style="flex: 1;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <div>
                <h2 style="margin: 0; font-size: 24px;">${user.name || user.username}</h2>
                <div style="color: var(--text-muted); font-size: 15px; margin-top: 4px;">@${user.username}</div>
                <div style="color: var(--text-secondary); margin-top: 8px;">${user.department || 'No department set'}</div>
              </div>
              <div>
                <div class="badge badge-success" style="font-size: 14px; padding: 6px 12px;">Rank: TBD</div>
              </div>
            </div>
            
            <div style="display: flex; gap: 32px; margin-top: 24px;">
              <div><strong style="font-size: 18px;">${user.score?.total || 0}</strong> <span style="color: var(--text-muted); font-size: 13px;">XP</span></div>
              <div><strong style="font-size: 18px;">${user.score?.merged_prs || 0}</strong> <span style="color: var(--text-muted); font-size: 13px;">PRs</span></div>
              <div><strong style="font-size: 18px;">${user.score?.issues_closed || 0}</strong> <span style="color: var(--text-muted); font-size: 13px;">Issues</span></div>
              <div><strong style="font-size: 18px;">${user.score?.reviews || 0}</strong> <span style="color: var(--text-muted); font-size: 13px;">Reviews</span></div>
            </div>
          </div>
        </div>
      `;

      // Render Heatmap (Mocked visual structure)
      const heatmapHtml = `
        <div class="card" style="margin-bottom: 24px;">
          <h3 style="margin-top: 0; font-size: 16px; color: var(--text-secondary);">Contribution Calendar</h3>
          <div style="display: flex; gap: 4px; overflow-x: auto; margin-top: 16px;">
            ${Array(30).fill(0).map(() => `
              <div style="display: flex; flex-direction: column; gap: 4px;">
                ${Array(7).fill(0).map(() => {
                  const intensity = Math.random();
                  const color = intensity > 0.8 ? '#196127' : intensity > 0.5 ? '#239a3b' : intensity > 0.2 ? '#7bc96f' : '#ebedf0';
                  return `<div style="width: 12px; height: 12px; background: ${color}; border-radius: 2px;"></div>`;
                }).join('')}
              </div>
            `).join('')}
          </div>
        </div>
      `;

      // Render timeline (Recent Contribs)
      const timelineHtml = `
        <div class="card">
          <h3 style="margin-top: 0; font-size: 16px; color: var(--text-secondary);">Recent Activity</h3>
          <div style="display: flex; flex-direction: column; gap: 16px; margin-top: 16px;">
            ${(contribs.contributions || []).slice(0, 10).map(c => `
              <div style="display: flex; gap: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--color-light-gray);">
                <div class="badge" style="background: var(--color-light-gray); height: max-content;">${c.type}</div>
                <div>
                  <div style="font-weight: 500;"><a href="${c.url}" target="_blank" style="color: var(--color-forest);">${c.title}</a></div>
                  <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">in ${c.repo} • ${new Date(c.merged_at || c.closed_at || c.submitted_at).toLocaleDateString()}</div>
                </div>
              </div>
            `).join('') || '<p style="color: var(--text-muted);">No recent activity.</p>'}
          </div>
        </div>
      `;

      detailsContainer.innerHTML = `
        ${headerHtml}
        ${heatmapHtml}
        ${timelineHtml}
      `;

    } catch (err) {
      detailsContainer.innerHTML = `<div class="card" style="color: var(--color-danger)">Error: ${err.message}</div>`;
    }
  });
}
