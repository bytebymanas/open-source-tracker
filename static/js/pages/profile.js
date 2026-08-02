/* ============================================================
   profile.js
   ============================================================ */
let _profileTab = 'contributions';

async function renderProfile() {
  const container = document.getElementById('profile-content');
  const username  = State.get('profileUsername');

  if (!username) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></div>
        <h3>No contributor selected</h3>
        <p>Click a contributor row in the Leaderboards or Contributors page</p>
      </div>`;
    return;
  }

  // Skeleton
  container.innerHTML = `
    <div class="profile-hero">
      <div class="avatar avatar-xl skeleton"></div>
      <div class="profile-meta">
        <div class="skeleton" style="width:200px;height:20px;margin-bottom:8px;"></div>
        <div class="skeleton" style="width:120px;height:13px;margin-bottom:16px;"></div>
        <div class="flex gap-4">
          ${[1,2,3].map(() => '<div class="skeleton" style="width:60px;height:32px;"></div>').join('')}
        </div>
      </div>
    </div>`;

  try {
    const [userResp, contribResp, repoResp] = await Promise.all([
      State.cache(`user-${username}`, () => API.user(username), 120000).catch(() => null),
      State.cache(`contribs-${username}`, () => API.contributions(username), 120000).catch(() => ({ contributions: [] })),
      State.cache(`repos-${username}`, () => API.repos(username), 120000).catch(() => ({ repos: [] })),
    ]);

    const user     = userResp || { login: username, name: username };
    const contribs = contribResp.contributions || [];
    const repos    = repoResp.repos || [];
    const prs      = contribs.filter(c => c.type === 'pull_request');
    const issues   = contribs.filter(c => c.type === 'issue');
    const totalScore = contribs.reduce((s, c) => s + (c.points || 0), 0);

    const avatarHtml = user.avatar_url
      ? `<div class="avatar avatar-xl"><img src="${escHtml(user.avatar_url)}" alt="${escHtml(user.login)}" loading="lazy"/></div>`
      : `<div class="avatar avatar-xl">${avatarInitials(user.name || user.login)}</div>`;

    container.innerHTML = `
      <div class="page-header page-header-row" style="margin-bottom:16px;">
        <div>
          <h1 class="page-title">${escHtml(user.name || user.login)}</h1>
          <p class="page-subtitle">@${escHtml(user.login || username)}</p>
        </div>
        <a href="https://github.com/${escHtml(username)}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm">
          ${Icons.ext} View on GitHub
        </a>
      </div>

      <div class="profile-hero">
        ${avatarHtml}
        <div class="profile-meta">
          <div class="profile-name">${escHtml(user.name || user.login)}</div>
          <div class="profile-handle">@${escHtml(user.login || username)}</div>
          <div class="profile-stats">
            <div>
              <div class="profile-stat-val text-accent">${totalScore}</div>
              <div class="profile-stat-label">Total Score</div>
            </div>
            <div>
              <div class="profile-stat-val">${prs.length}</div>
              <div class="profile-stat-label">Merged PRs</div>
            </div>
            <div>
              <div class="profile-stat-val">${issues.length}</div>
              <div class="profile-stat-label">Issues</div>
            </div>
            <div>
              <div class="profile-stat-val">${repos.length}</div>
              <div class="profile-stat-label">Repos</div>
            </div>
          </div>
        </div>
      </div>

      <div class="tabs" id="profile-tabs">
        <button class="tab-btn ${_profileTab === 'contributions' ? 'active' : ''}" data-tab="contributions">Contributions (${contribs.length})</button>
        <button class="tab-btn ${_profileTab === 'repos' ? 'active' : ''}" data-tab="repos">Repositories (${repos.length})</button>
      </div>

      <div id="profile-tab-content"></div>`;

    _renderProfileTab(contribs, repos);

    container.querySelectorAll('[data-tab]').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('[data-tab]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        _profileTab = btn.dataset.tab;
        _renderProfileTab(contribs, repos);
      });
    });

  } catch (err) {
    container.innerHTML = `<div class="card">${errorState(err, 'renderProfile()')}</div>`;
  }
}

function _renderProfileTab(contribs, repos) {
  const el = document.getElementById('profile-tab-content');
  if (!el) return;

  if (_profileTab === 'contributions') {
    if (!contribs.length) {
      el.innerHTML = `<div class="card">
        <div class="empty-state">
          <div class="empty-state-icon">${Icons.pr}</div>
          <h3>No contributions found</h3>
          <p>This contributor has no tracked contributions yet</p>
        </div>
      </div>`;
      return;
    }

    const rows = contribs.map(c => {
      const isPR = c.type === 'pull_request';
      return `
        <div class="contrib-item">
          <div class="contrib-icon ${isPR ? 'pr' : 'issue'}">${isPR ? Icons.pr : Icons.issue}</div>
          <div class="contrib-body">
            <div class="contrib-title">
              ${c.url
                ? `<a href="${escHtml(c.url)}" target="_blank" rel="noopener">${escHtml(c.title || 'Untitled')}</a>`
                : escHtml(c.title || 'Untitled')}
            </div>
            <div class="contrib-meta">
              ${c.repo ? escHtml(c.repo) + ' · ' : ''}
              <span class="badge ${isPR ? 'badge-primary' : 'badge-info'}">${isPR ? 'PR' : 'Issue'}</span>
            </div>
          </div>
          <div class="contrib-points">+${c.points || 0}</div>
        </div>`;
    }).join('');

    el.innerHTML = `<div class="card"><div class="contrib-list">${rows}</div></div>`;
  } else {
    // Repos tab
    if (!repos.length) {
      el.innerHTML = `<div class="card">
        <div class="empty-state">
          <div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 6h-1V4c0-1.1-.9-2-2-2H3c-1.1 0-2 .9-2 2v13c0 1.1.9 2 2 2h1v1c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zM3 4h14v2H3V4zm17 16H6v-1h11c1.1 0 2-.9 2-2V8h1v12z"/></svg></div>
          <h3>No public repositories</h3>
        </div>
      </div>`;
      return;
    }

    const cards = repos.map(r => `
      <div class="repo-card">
        <div class="repo-card-name">
          ${r.url
            ? `<a href="${escHtml(r.url)}" target="_blank" rel="noopener">${escHtml(r.name)}</a>`
            : escHtml(r.name)}
          ${r.is_fork ? `<span class="badge badge-neutral" style="margin-left:6px;font-size:10px;">Fork</span>` : ''}
        </div>
        <div class="repo-card-desc">${escHtml(r.description || 'No description provided.')}</div>
        <div class="repo-card-meta">
          ${r.language ? `<span><span class="lang-dot"></span>${escHtml(r.language)}</span>` : ''}
          <span>⭐ ${r.stars || 0}</span>
          <span>🍴 ${r.forks || 0}</span>
        </div>
      </div>`).join('');

    el.innerHTML = `<div class="repo-grid">${cards}</div>`;
  }
}
