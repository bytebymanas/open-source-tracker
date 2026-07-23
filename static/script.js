/**
 * Open Source Contribution Tracker - Frontend Logic
 * CUSoC 2026
 */

const API_BASE = "";

// DOM refs - Navigation
const navLeaderboard    = document.getElementById("nav-leaderboard");
const navProfile        = document.getElementById("nav-profile");
const viewLeaderboard   = document.getElementById("view-leaderboard");
const viewProfile       = document.getElementById("view-profile");

// DOM refs - Status
const apiStatusDot      = document.querySelector(".status-dot");
const apiStatusText     = document.querySelector(".status-text");

// DOM refs - Leaderboard
const leaderboardBody   = document.getElementById("leaderboard-body");
const leaderboardEmpty  = document.getElementById("leaderboard-empty");
const tableCount        = document.getElementById("table-count");
const leaderboardSearch = document.getElementById("leaderboard-search");
const deptSelect        = document.getElementById("dept-filter");
const periodBtns        = document.querySelectorAll(".filter-btn[data-period]");
const statTotalUsers    = document.getElementById("stat-total-users");
const statTotalPRs      = document.getElementById("stat-total-prs");
const statTotalIssues   = document.getElementById("stat-total-issues");
const statTopScore      = document.getElementById("stat-top-score");

// DOM refs - Profile
const profileInput      = document.getElementById("profile-username-input");
const profileSearchBtn  = document.getElementById("profile-search-btn");
const profileCard       = document.getElementById("profile-card");
const profileLoading    = document.getElementById("profile-loading");
const profileError      = document.getElementById("profile-error");
const profileErrorMsg   = document.getElementById("profile-error-msg");

// State
let allRows          = [];
let currentPeriod    = "all_time";
let currentDept      = "";


// Navigation
function showView(name) {
  const isLeaderboard = name === "leaderboard";
  viewLeaderboard.classList.toggle("active", isLeaderboard);
  viewProfile.classList.toggle("active", !isLeaderboard);
  navLeaderboard.classList.toggle("active", isLeaderboard);
  navProfile.classList.toggle("active", !isLeaderboard);
}

navLeaderboard.addEventListener("click", (e) => { e.preventDefault(); showView("leaderboard"); });
navProfile.addEventListener("click",     (e) => { e.preventDefault(); showView("profile"); });


// API helpers
async function apiFetch(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.message || `HTTP ${res.status}`);
  }
  return res.json();
}


// Health check
async function checkHealth() {
  try {
    await apiFetch("/api/health");
    apiStatusDot.className   = "status-dot online";
    apiStatusText.textContent = "API online";
  } catch {
    apiStatusDot.className   = "status-dot offline";
    apiStatusText.textContent = "API offline";
  }
}


// Leaderboard
async function loadLeaderboard(period = "all_time", department = "") {
  renderSkeletons();
  leaderboardSearch.value = "";
  updateFilterChip(department);
  let url = `/api/leaderboard?period=${period}`;
  if (department) url += `&department=${encodeURIComponent(department)}`;
  try {
    const data = await apiFetch(url);
    allRows = data.leaderboard || [];
    renderTable(allRows);
    updateStats(allRows);
  } catch (err) {
    leaderboardBody.innerHTML = `
      <tr><td colspan="8" style="text-align:center;padding:32px;color:var(--color-error)">
        Failed to load leaderboard: ${err.message}
      </td></tr>`;
  }
}

// Departments
async function loadDepartments() {
  try {
    const data = await apiFetch("/api/departments");
    const depts = data.departments || [];
    // Rebuild options — keep the "All Departments" default at top
    deptSelect.innerHTML = '<option value="">All Departments</option>';
    depts.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = d;
      deptSelect.appendChild(opt);
    });
  } catch {
    // Non-fatal: dropdown stays with the default option
  }
}

function renderSkeletons() {
  leaderboardBody.innerHTML = Array(5).fill(`
    <tr class="skeleton-row"><td colspan="8"><div class="skeleton"></div></td></tr>`).join("");
  leaderboardEmpty.classList.add("hidden");
  tableCount.textContent = "Loading...";
}

function renderTable(rows) {
  if (rows.length === 0) {
    leaderboardBody.innerHTML = "";
    leaderboardEmpty.classList.remove("hidden");
    tableCount.textContent = "0 contributors";
    return;
  }
  leaderboardEmpty.classList.add("hidden");
  tableCount.textContent = `${rows.length} contributor${rows.length !== 1 ? "s" : ""}`;
  leaderboardBody.innerHTML = rows.map((entry, idx) => {
    const rank      = entry.rank || idx + 1;
    const rankClass = rank === 1 ? "rank-1" : rank === 2 ? "rank-2" : rank === 3 ? "rank-3" : "";
    const avatar    = entry.avatar_url || `https://github.com/${entry.username}.png?size=60`;
    const name      = entry.name || "";
    const username  = entry.username || "";
    const dept      = entry.department || "";
    const score     = entry.total_score ?? 0;
    const prs       = entry.merged_prs ?? 0;
    const issues    = entry.issues_closed ?? 0;
    const reviews   = entry.reviews ?? 0;
    const deptCell  = dept
      ? `<span class="dept-badge">${escapeHtml(dept)}</span>`
      : `<span class="dept-badge dept-badge-empty">—</span>`;
    return `<tr>
      <td><span class="rank-cell ${rankClass}">#${rank}</span></td>
      <td>
        <div class="user-cell">
          <img class="user-avatar" src="${avatar}" alt="${username}" loading="lazy"
               onerror="this.src='https://github.com/identicons/${username}.png'" />
          <div class="user-info">
            <span class="user-login">${username}</span>
            ${name ? `<span class="user-name">${name}</span>` : ""}
          </div>
        </div>
      </td>
      <td>${deptCell}</td>
      <td><span class="score-cell">${score}</span></td>
      <td><span class="num-cell">${prs}</span></td>
      <td><span class="num-cell">${issues}</span></td>
      <td><span class="num-cell">${reviews}</span></td>
      <td class="action-cell">
        <button class="btn-view" onclick="openProfile('${username}')">View</button>
      </td>
    </tr>`;
  }).join("");
}

function updateFilterChip(department) {
  const bar      = document.getElementById("active-filters");
  const chipText = document.getElementById("dept-chip-text");
  if (department) {
    chipText.textContent = department;
    bar.style.display = "flex";
  } else {
    bar.style.display = "none";
  }
}

function updateStats(rows) {
  statTotalUsers.textContent  = rows.length;
  statTotalPRs.textContent    = rows.reduce((s, r) => s + (r.merged_prs ?? 0), 0);
  statTotalIssues.textContent = rows.reduce((s, r) => s + (r.issues_closed ?? 0), 0);
  statTopScore.textContent    = rows.length > 0 ? (rows[0].total_score ?? 0) : 0;
}


// Filtering — username search (client-side over already-loaded rows)
leaderboardSearch.addEventListener("input", () => {
  const q = leaderboardSearch.value.trim().toLowerCase();
  const filtered = q ? allRows.filter(r => (r.username || "").toLowerCase().includes(q)) : allRows;
  renderTable(filtered);
});

// Period filter
periodBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    periodBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentPeriod = btn.dataset.period;
    loadLeaderboard(currentPeriod, currentDept);
  });
});

// Department filter
deptSelect.addEventListener("change", () => {
  currentDept = deptSelect.value;
  loadLeaderboard(currentPeriod, currentDept);
});

// Clear filter chip
document.getElementById("dept-chip-clear").addEventListener("click", () => {
  currentDept = "";
  deptSelect.value = "";
  loadLeaderboard(currentPeriod, currentDept);
});


// Profile
function openProfile(username) {
  showView("profile");
  profileInput.value = username;
  fetchProfile(username);
}

async function fetchProfile(username) {
  if (!username) return;

  profileCard.classList.add("hidden");
  profileError.classList.add("hidden");
  profileLoading.classList.remove("hidden");
  profileSearchBtn.disabled = true;

  resetContributions();
  resetRepos();

  try {
    const data = await apiFetch(`/api/user/${encodeURIComponent(username)}`);

    document.getElementById("profile-avatar").src       = data.avatar_url || "";
    document.getElementById("profile-name").textContent = data.name || data.username;

    const usernameLink = document.getElementById("profile-username-link");
    usernameLink.textContent = `@${data.username}`;
    usernameLink.href        = `https://github.com/${data.username}`;

    document.getElementById("profile-repos").textContent       = `${data.public_repos ?? 0} public repos`;
    document.getElementById("profile-total-score").textContent = data.score?.total ?? 0;
    document.getElementById("profile-prs").textContent         = data.score?.merged_prs ?? 0;
    document.getElementById("profile-issues").textContent      = data.score?.issues_closed ?? 0;
    document.getElementById("profile-reviews").textContent     = data.score?.reviews ?? 0;

    profileCard.classList.remove("hidden");

    // Fetch sub-sections in parallel
    fetchContributions(username);
    fetchRepos(username);

  } catch (err) {
    profileErrorMsg.textContent = err.message || "Failed to fetch user data.";
    profileError.classList.remove("hidden");
  } finally {
    profileLoading.classList.add("hidden");
    profileSearchBtn.disabled = false;
  }
}


// Contributions breakdown
function resetContributions() {
  document.getElementById("contrib-loading").classList.add("hidden");
  document.getElementById("contrib-table").classList.add("hidden");
  document.getElementById("contrib-empty").classList.add("hidden");
  document.getElementById("contrib-count").textContent = "—";
  document.getElementById("contrib-body").innerHTML = "";
}

async function fetchContributions(username) {
  const loadingEl = document.getElementById("contrib-loading");
  const tableEl   = document.getElementById("contrib-table");
  const emptyEl   = document.getElementById("contrib-empty");
  const bodyEl    = document.getElementById("contrib-body");
  const countEl   = document.getElementById("contrib-count");

  loadingEl.classList.remove("hidden");

  try {
    const data  = await apiFetch(`/api/user/${encodeURIComponent(username)}/contributions`);
    const items = data.contributions || [];
    countEl.textContent = `${items.length} total`;

    if (items.length === 0) {
      emptyEl.classList.remove("hidden");
      return;
    }

    bodyEl.innerHTML = items.map(item => {
      const contribId = item.id;
      const ispr  = item.type === "pull_request";
      const badge = ispr
        ? `<span class="contrib-type-badge badge-pr">PR</span>`
        : `<span class="contrib-type-badge badge-issue">Issue</span>`;
      const titleHtml = item.title
        ? `<a href="${item.url}" target="_blank" rel="noopener" class="contrib-title">${escapeHtml(item.title)}</a>`
        : `<span class="contrib-title">—</span>`;

      const rowId  = `annot-row-${contribId}`;
      const formId = `annot-form-${contribId}`;

      return `<tr data-contrib-id="${contribId}">
        <td>${badge}</td>
        <td>${titleHtml}</td>
        <td><span class="contrib-repo">${escapeHtml(item.repo || "—")}</span></td>
        <td><span class="contrib-pts">+${item.points}</span></td>
        <td class="action-cell">
          <button class="btn-annotate" id="btn-annot-${contribId}"
            onclick="toggleAnnotationForm(${contribId})">Annotate</button>
        </td>
      </tr>
      <tr class="annot-form-row hidden" id="${rowId}">
        <td colspan="5">
          <div class="annot-form" id="${formId}">
            <div class="annot-form-header">
              <span class="annot-form-title">Add Mentor Annotation</span>
              <span class="annot-form-id">Contribution #${contribId}</span>
            </div>
            <div class="annot-fields">
              <div class="annot-field">
                <label class="annot-label" for="annot-mentor-${contribId}">Mentor Username <span class="annot-required">*</span></label>
                <input type="text" id="annot-mentor-${contribId}" class="annot-input"
                  placeholder="github_username" autocomplete="off" spellcheck="false" />
              </div>
              <div class="annot-field annot-field-grow">
                <label class="annot-label" for="annot-note-${contribId}">Note</label>
                <textarea id="annot-note-${contribId}" class="annot-textarea"
                  placeholder="Quality feedback, concerns, or observations..." rows="2"></textarea>
              </div>
              <div class="annot-field annot-field-narrow">
                <label class="annot-label" for="annot-override-${contribId}">Score Override</label>
                <input type="number" id="annot-override-${contribId}" class="annot-input"
                  placeholder="—" min="0" max="100" />
              </div>
            </div>
            <div class="annot-footer">
              <label class="annot-checkbox-label">
                <input type="checkbox" id="annot-verified-${contribId}" class="annot-checkbox" />
                <span>Mark as verified</span>
              </label>
              <div class="annot-actions">
                <span class="annot-feedback hidden" id="annot-feedback-${contribId}"></span>
                <button class="btn-secondary" onclick="toggleAnnotationForm(${contribId})">Cancel</button>
                <button class="btn-primary btn-sm" onclick="submitAnnotation(${contribId})">Submit</button>
              </div>
            </div>
          </div>
        </td>
      </tr>`;
    }).join("");

    tableEl.classList.remove("hidden");
  } catch (err) {
    countEl.textContent = "error";
    emptyEl.querySelector(".empty-body").textContent = `Failed to load: ${err.message}`;
    emptyEl.classList.remove("hidden");
  } finally {
    loadingEl.classList.add("hidden");
  }
}

function toggleAnnotationForm(contribId) {
  const row = document.getElementById(`annot-row-${contribId}`);
  if (!row) return;
  const isHidden = row.classList.toggle("hidden");
  const btn = document.getElementById(`btn-annot-${contribId}`);
  if (btn) btn.textContent = isHidden ? "Annotate" : "Cancel";
}

async function submitAnnotation(contribId) {
  const mentorInput    = document.getElementById(`annot-mentor-${contribId}`);
  const noteInput      = document.getElementById(`annot-note-${contribId}`);
  const verifiedInput  = document.getElementById(`annot-verified-${contribId}`);
  const overrideInput  = document.getElementById(`annot-override-${contribId}`);
  const feedbackEl     = document.getElementById(`annot-feedback-${contribId}`);

  const mentor = mentorInput.value.trim();
  if (!mentor) {
    showAnnotFeedback(feedbackEl, "Mentor username is required.", false);
    mentorInput.focus();
    return;
  }

  const payload = {
    mentor_username: mentor,
    note:            noteInput.value.trim() || null,
    verified:        verifiedInput.checked ? 1 : 0,
    score_override:  overrideInput.value !== "" ? parseInt(overrideInput.value, 10) : null,
  };

  const submitBtn = document.querySelector(`#annot-form-${contribId} .btn-primary`);
  if (submitBtn) submitBtn.disabled = true;

  try {
    const res = await fetch(`/api/contributions/${contribId}/annotations`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      showAnnotFeedback(feedbackEl, body.message || `Error ${res.status}`, false);
    } else {
      showAnnotFeedback(feedbackEl, "Annotation saved.", true);
      noteInput.value      = "";
      verifiedInput.checked = false;
      overrideInput.value  = "";
    }
  } catch {
    showAnnotFeedback(feedbackEl, "Network error. Try again.", false);
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function showAnnotFeedback(el, msg, success) {
  el.textContent = msg;
  el.className = `annot-feedback ${success ? "annot-feedback-ok" : "annot-feedback-err"}`;
}


// Repositories
function resetRepos() {
  document.getElementById("repos-loading").classList.add("hidden");
  document.getElementById("repos-grid").classList.add("hidden");
  document.getElementById("repos-empty").classList.add("hidden");
  document.getElementById("repos-count").textContent = "—";
  document.getElementById("repos-grid").innerHTML = "";
}

async function fetchRepos(username) {
  const loadingEl = document.getElementById("repos-loading");
  const gridEl    = document.getElementById("repos-grid");
  const emptyEl   = document.getElementById("repos-empty");
  const countEl   = document.getElementById("repos-count");

  loadingEl.classList.remove("hidden");

  try {
    const data  = await apiFetch(`/api/user/${encodeURIComponent(username)}/repos`);
    const repos = data.repos || [];
    countEl.textContent = `${repos.length} repos`;

    if (repos.length === 0) {
      emptyEl.classList.remove("hidden");
      return;
    }

    gridEl.innerHTML = repos.slice(0, 12).map(repo => `
      <a href="${repo.url}" target="_blank" rel="noopener" class="repo-card">
        <span class="repo-name">${escapeHtml(repo.name)}</span>
        ${repo.description ? `<span class="repo-desc">${escapeHtml(repo.description)}</span>` : ""}
        <div class="repo-meta">
          <span class="repo-meta-item">
            <span class="lang-dot" style="background:${langColor(repo.language)}"></span>
            ${escapeHtml(repo.language)}
          </span>
          <span class="repo-meta-item">&#9733; ${repo.stars}</span>
          ${repo.forks ? `<span class="repo-meta-item">&#8627; ${repo.forks}</span>` : ""}
        </div>
      </a>`).join("");

    gridEl.classList.remove("hidden");
  } catch (err) {
    countEl.textContent = "error";
    emptyEl.querySelector(".empty-body").textContent = `Failed to load: ${err.message}`;
    emptyEl.classList.remove("hidden");
  } finally {
    loadingEl.classList.add("hidden");
  }
}


// Utilities
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const LANG_COLORS = {
  Python: "#3572A5", JavaScript: "#f1e05a", TypeScript: "#2b7489",
  Java: "#b07219", Go: "#00ADD8", Rust: "#dea584", C: "#555555",
  "C++": "#f34b7d", Ruby: "#701516", HTML: "#e34c26", CSS: "#563d7c",
  Shell: "#89e051", Swift: "#ffac45", Kotlin: "#A97BFF",
};

function langColor(lang) {
  return LANG_COLORS[lang] || "var(--color-text-faint)";
}

profileSearchBtn.addEventListener("click", () => {
  const username = profileInput.value.trim();
  if (username) fetchProfile(username);
});

profileInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const username = profileInput.value.trim();
    if (username) fetchProfile(username);
  }
});


// Init
(async function init() {
  await checkHealth();
  await loadDepartments();
  await loadLeaderboard(currentPeriod, currentDept);
})();
