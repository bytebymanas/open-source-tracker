/* ============================================================
   reviews.js — Mentor annotations/reviews
   ============================================================ */
async function renderReviews() {
  setupReviewsListeners();
  await loadReviews();
}

function setupReviewsListeners() {
  const verifiedEl = document.getElementById('reviews-filter-verified');
  const studentEl  = document.getElementById('reviews-filter-student');
  if (verifiedEl && !verifiedEl._bound) {
    verifiedEl._bound = true;
    verifiedEl.addEventListener('change', loadReviews);
  }
  if (studentEl && !studentEl._bound) {
    studentEl._bound = true;
    studentEl.addEventListener('input', debounce(loadReviews, 300));
  }
}

async function loadReviews() {
  const list = document.getElementById('reviews-list');
  list.innerHTML = `<div class="card"><div class="skeleton-row"><div class="skeleton-text"><div class="skeleton" style="width:100%;"></div></div></div></div>`;

  const verified = document.getElementById('reviews-filter-verified')?.value;
  const student  = document.getElementById('reviews-filter-student')?.value?.trim() || '';

  let qs = '?';
  if (verified !== '' && verified !== null && verified !== undefined) qs += `verified=${verified}&`;
  if (student) qs += `student=${encodeURIComponent(student)}&`;

  try {
    const data = await API.annotations(qs.length > 1 ? qs : '');
    const annotations = data.annotations || [];

    if (!annotations.length) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 9h-2V5h2v6zm0 4h-2v-2h2v2z"/></svg></div>
          <h3>No annotations found</h3>
          <p>Mentor annotations will appear here once contributions are reviewed</p>
        </div>`;
      return;
    }

    list.innerHTML = annotations.map(a => {
      const isPR = a.contribution_type === 'pull_request';
      return `
        <div class="review-card">
          <div class="review-card-header">
            <div class="contrib-icon ${isPR ? 'pr' : 'issue'}" style="width:28px;height:28px;">
              ${isPR ? Icons.pr : Icons.issue}
            </div>
            <div class="review-card-title">${escHtml(a.contribution_title || a.contribution_url || 'Contribution')}</div>
            <span class="badge ${a.verified ? 'badge-success' : 'badge-warning'}">${a.verified ? '✓ Verified' : 'Pending'}</span>
            ${a.score_override != null ? `<span class="badge badge-info">Override: ${a.score_override} pts</span>` : ''}
            <button class="btn btn-danger btn-sm" data-del-annotation="${a.id}" aria-label="Delete annotation">Delete</button>
          </div>
          <div class="review-card-body">
            <div class="review-card-field"><strong>Student</strong>@${escHtml(a.student_username || '—')}</div>
            <div class="review-card-field"><strong>Reviewer</strong>@${escHtml(a.mentor_username || '—')}</div>
            <div class="review-card-field"><strong>Type</strong><span class="badge ${isPR ? 'badge-primary' : 'badge-info'}">${isPR ? 'Pull Request' : 'Issue'}</span></div>
            ${a.note ? `<div class="review-note">"${escHtml(a.note)}"</div>` : ''}
          </div>
        </div>`;
    }).join('');

    // Delete annotation
    list.querySelectorAll('[data-del-annotation]').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('Remove this annotation?')) return;
        try {
          await API.deleteAnnotation(btn.dataset.delAnnotation);
          showToast('Annotation removed');
          await loadReviews();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });

  } catch (err) {
    list.innerHTML = `<div class="card">${errorState(err, 'loadReviews()')}</div>`;
  }
}
