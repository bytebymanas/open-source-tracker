/* ============================================================
   settings.js — Scoring weights + platform info
   ============================================================ */
async function renderSettings() {
  await Promise.all([loadWeights(), loadRateLimit()]);
}

async function loadWeights() {
  const body = document.getElementById('weights-body');
  body.innerHTML = `<div class="skeleton" style="height:200px;"></div>`;

  try {
    const data = await API.weights();
    const weights = data.weights || {};

    const LABELS = {
      pr_points:            { label: 'Merged PR',           desc: 'Points per merged pull request'         },
      issue_points:         { label: 'Closed Issue',        desc: 'Points per closed issue'                },
      review_points:        { label: 'Code Review',         desc: 'Points per approved code review'        },
      first_contrib_bonus:  { label: 'First Contribution',  desc: 'Bonus points on first contribution ever'},
    };

    if (!Object.keys(weights).length) {
      body.innerHTML = `<div class="empty-state" style="padding:24px;"><h3>No weights configured</h3></div>`;
      return;
    }

    body.innerHTML = Object.entries(weights).map(([key, val]) => {
      const info = LABELS[key] || { label: key, desc: '' };
      return `
        <div class="settings-row">
          <div>
            <div class="settings-row-label">${escHtml(info.label)}</div>
            ${info.desc ? `<div class="settings-row-desc">${escHtml(info.desc)}</div>` : ''}
          </div>
          <div class="settings-row-control">
            <input type="number" class="input weight-input"
              data-weight-key="${escHtml(key)}"
              value="${Number(val)}" min="0" step="1"
              aria-label="${escHtml(info.label)} weight"/>
          </div>
        </div>`;
    }).join('');

  } catch (err) {
    body.innerHTML = `${errorState(err, 'loadWeights()')}`;
  }
}

async function loadRateLimit() {
  const el = document.getElementById('rate-limit-desc');
  if (!el) return;
  try {
    const data = await API.rateLimit();
    const rl   = data.github_rate_limit || {};
    el.textContent = `${rl.remaining ?? '?'} / ${rl.limit ?? '?'} requests remaining`;
  } catch (_) {
    el.textContent = 'Unable to fetch';
  }
}

document.getElementById('save-weights-btn')?.addEventListener('click', async () => {
  const inputs = document.querySelectorAll('[data-weight-key]');
  const payload = {};
  inputs.forEach(inp => { payload[inp.dataset.weightKey] = parseFloat(inp.value) || 0; });

  const btn = document.getElementById('save-weights-btn');
  btn.disabled    = true;
  btn.textContent = 'Saving…';

  try {
    await API.updateWeights(payload);
    showToast('Scoring weights saved');
    State.invalidate();   // scores change — bust full cache
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Save Changes';
  }
});
