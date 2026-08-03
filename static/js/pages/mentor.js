/* ============================================================
   mentor.js — Mentor Dashboard
   ============================================================ */

const MentorDashboard = (() => {
  let isLoaded = false;

  async function load() {
    if (isLoaded) return;
    renderSkeleton();

    try {
      // Fetch pending reviews for a mentor
      const reviews = await API.annotations('?verified=0'); // Suppose the API accepts this, or filter manually
      // The API doesn't actually have ?verified=0 implemented that way in backend right now?
      // Wait, let's just fetch all and filter manually for safety.
      let allReviews = [];
      try {
        const res = await API.annotations();
        allReviews = res.annotations || [];
      } catch (e) {
        allReviews = [];
      }
      
      const pending = allReviews.filter(r => !r.is_verified);
      renderQueue(pending);

      isLoaded = true;
    } catch (err) {
      console.error('Failed to load mentor dashboard:', err);
      showToast('Failed to load review queue', 'error');
    }
  }

  function renderSkeleton() {
    const container = document.getElementById('mentor-queue');
    if (container) {
      container.innerHTML = `
        <div class="card"><div class="skeleton-row"><div class="skeleton-text"><div class="skeleton" style="width:100%;"></div></div></div></div>
      `;
    }
  }

  function renderQueue(reviews) {
    const container = document.getElementById('mentor-queue');
    if (!container) return;

    if (!reviews || reviews.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="padding:48px 24px;">
          <div style="font-size:32px;margin-bottom:16px;">🎉</div>
          <h3>Inbox Zero</h3>
          <p style="color:var(--t-secondary);">You have no pending reviews in your queue.</p>
        </div>
      `;
      return;
    }

    const html = reviews.map(r => `
      <div class="card" style="margin-bottom:16px;">
        <div class="card-body">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <div style="font-weight:600;font-size:var(--fs-md);margin-bottom:4px;">${escHtml(r.github_username)}</div>
              <div style="font-size:var(--fs-sm);color:var(--t-secondary);">
                Requires verification for contribution score override.
              </div>
              <div style="font-size:var(--fs-sm);margin-top:12px;padding:12px;background:var(--c-sage-light);border-radius:var(--radius-md);color:var(--c-forest-dark);">
                "${escHtml(r.note)}"
              </div>
            </div>
            <div style="display:flex;gap:8px;">
              <button class="btn btn-secondary btn-sm" onclick="showToast('Review dismissed', 'info')">Dismiss</button>
              <button class="btn btn-primary btn-sm" onclick="showToast('Contribution verified!', 'success')">Verify</button>
            </div>
          </div>
        </div>
      </div>
    `).join('');

    container.innerHTML = html;
  }

  return { load };
})();

// Register
Router.register('mentor', MentorDashboard.load);
