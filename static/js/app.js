/* ============================================================
   app.js — Bootstrap, route registration, global wiring
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {

  /* ---- Register routes ---- */
  Router.register('dashboard',    renderDashboard);
  Router.register('leaderboards', renderLeaderboards);
  Router.register('contributors', renderContributors);
  Router.register('activity',     renderActivity);
  Router.register('profile',      renderProfile);
  Router.register('reviews',      renderReviews);
  Router.register('goals',        renderGoals);
  Router.register('settings',     renderSettings);

  /* ---- Initial navigation from hash ---- */
  const hash = location.hash.replace('#', '').trim();
  Router.navigate(hash || 'dashboard', false);

  /* ---- Global search (Enter → profile lookup) ---- */
  const searchEl = document.getElementById('global-search');
  searchEl?.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const q = searchEl.value.trim().replace(/^@/, '');
    if (!q) return;
    searchEl.value = '';
    State.set('profileUsername', q);
    Router.navigate('profile');
  });

  /* ---- Contributors page "Import" button also opens modal ---- */

  /* ---- Header avatar → profile ---- */
  document.getElementById('header-avatar')?.addEventListener('click', () => {
    Router.navigate('profile');
  });

  /* ---- Sidebar profile link ---- */
  const sidebarProfileLink = document.getElementById('nav-profile-link');
  if (sidebarProfileLink) {
    sidebarProfileLink.addEventListener('click', () => Router.navigate('profile'));
    sidebarProfileLink.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') Router.navigate('profile');
    });
  }

  /* ---- Sidebar "View all →" buttons on dashboard card ---- */
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-page]');
    if (btn && btn.tagName === 'BUTTON' && !btn.closest('.modal-overlay')) {
      e.preventDefault();
      Router.navigate(btn.dataset.page);
    }
  });
});
