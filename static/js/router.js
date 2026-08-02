/* ============================================================
   router.js — SPA router, modal/drawer manager, shared utils
   ============================================================ */

/* ---- Router ---- */
const Router = (() => {
  const routes = {};
  let currentPage = null;

  function navigate(page, push = true) {
    if (!routes[page]) page = 'dashboard';
    if (currentPage === page && page !== 'profile') return;
    currentPage = page;

    // Hide all pages
    document.querySelectorAll('.page-view').forEach(s => s.classList.remove('active'));

    // Show target page
    const section = document.getElementById('page-' + page);
    if (section) section.classList.add('active');

    // Update sidebar nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navEl = document.getElementById('nav-' + page)
                || document.querySelector(`.nav-item[data-page="${page}"]`);
    if (navEl) navEl.classList.add('active');

    // Breadcrumb
    const TITLES = {
      dashboard: 'Dashboard', leaderboards: 'Leaderboards', contributors: 'Contributors',
      activity: 'Activity Feed', profile: 'Profile', reviews: 'Mentor Reviews',
      goals: 'Goals', settings: 'Settings',
    };
    const titleEl = document.getElementById('header-page-title');
    if (titleEl) titleEl.textContent = TITLES[page] || page;

    // Update hash
    if (push) history.pushState({ page }, '', '#' + page);

    // Render page
    if (routes[page]) routes[page]();
  }

  function register(page, fn) { routes[page] = fn; }

  window.addEventListener('popstate', (e) => {
    const p = e.state?.page || location.hash.replace('#', '') || 'dashboard';
    navigate(p, false);
  });

  return { navigate, register };
})();

/* ---- Global click delegation ---- */
document.addEventListener('click', (e) => {
  // Nav items
  const navBtn = e.target.closest('[data-page]');
  if (navBtn && !navBtn.closest('.modal-overlay') && !navBtn.closest('.drawer')) {
    e.preventDefault();
    Router.navigate(navBtn.dataset.page);
    return;
  }
  // Close modal buttons
  const closeBtn = e.target.closest('[data-close-modal]');
  if (closeBtn) { closeModal(closeBtn.dataset.closeModal); return; }
  // Click outside modal
  if (e.target.classList.contains('modal-overlay')) {
    e.target.style.display = 'none';
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay[style*="flex"]').forEach(m => {
      m.style.display = 'none';
    });
    closeActiveDrawer();
  }
});

/* ---- Modal helpers ---- */
function openModal(id) {
  const el = document.getElementById(id);
  if (el) { el.style.display = 'flex'; }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) { el.style.display = 'none'; }
}

/* ---- Drawer ---- */
let _activeDrawer = null;

function openDrawer({ title, content, footer }) {
  closeActiveDrawer();
  const overlay = document.createElement('div');
  overlay.className = 'drawer-overlay';
  overlay.id = 'active-drawer-overlay';

  const drawer = document.createElement('div');
  drawer.className = 'drawer';
  drawer.id = 'active-drawer';
  drawer.innerHTML = `
    <div class="drawer-header">
      <span class="drawer-title">${title}</span>
      <button class="drawer-close" id="drawer-close-btn" aria-label="Close drawer">&times;</button>
    </div>
    <div class="drawer-body">${content}</div>
    ${footer ? `<div class="drawer-footer">${footer}</div>` : ''}
  `;

  document.body.appendChild(overlay);
  document.body.appendChild(drawer);
  _activeDrawer = { overlay, drawer };

  overlay.addEventListener('click', closeActiveDrawer);
  document.getElementById('drawer-close-btn')?.addEventListener('click', closeActiveDrawer);
}

function closeActiveDrawer() {
  if (!_activeDrawer) return;
  _activeDrawer.overlay.remove();
  _activeDrawer.drawer.remove();
  _activeDrawer = null;
}

/* ---- Toast ---- */
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<span class="toast-icon">${icon}</span><span>${escHtml(String(message))}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 300ms';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

/* ---- Shared utilities ---- */
function escHtml(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function avatarInitials(name) {
  return (name || '?').split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase();
}

function relativeTime(isoStr) {
  if (!isoStr) return '—';
  const s = Math.floor((Date.now() - new Date(isoStr)) / 1000);
  if (s < 60)    return `${s}s ago`;
  if (s < 3600)  return `${Math.floor(s/60)}m ago`;
  if (s < 86400) return `${Math.floor(s/3600)}h ago`;
  if (s < 604800)return `${Math.floor(s/86400)}d ago`;
  return new Date(isoStr).toLocaleDateString();
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

/* ---- SVG icons ---- */
const Icons = {
  pr: `<svg viewBox="0 0 24 24" fill="currentColor" width="15" height="15"><path d="M6 3a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm0 2a1 1 0 1 1 0 2 1 1 0 0 1 0-2zm12-2a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm0 2a1 1 0 1 1 0 2 1 1 0 0 1 0-2zM6 9c-1.654 0-3 1.346-3 3v7h2v-7c0-.551.449-1 1-1h1.586l4.707 4.707-1.293 1.293L9 15H7v2h2.414L15 11.414V9.586L9.707 4.293A.997.997 0 0 0 9 4H6z"/></svg>`,
  issue: `<svg viewBox="0 0 24 24" fill="currentColor" width="15" height="15"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-9.5c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5-.67-1.5-1.5-1.5z"/></svg>`,
  ext: `<svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13"><path d="M19 19H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>`,
};
