/**
 * Open Source Contribution Tracker — Frontend Logic
 * CUSoC 2026
 *
 * Handles:
 *  - Navigation between leaderboard and profile views
 *  - Fetching leaderboard data from /api/leaderboard
 *  - Fetching user profile data from /api/user/<username>
 *  - Rendering tables, stats, and profile cards
 *  - Filtering and sorting the leaderboard table
 */

const API_BASE = "";  // Same origin; Flask serves both API and static

// ── DOM refs ────────────────────────────────────────────────────
const navLeaderboard     = document.getElementById("nav-leaderboard");
const navProfile         = document.getElementById("nav-profile");
const viewLeaderboard    = document.getElementById("view-leaderboard");
const viewProfile        = document.getElementById("view-profile");

const apiStatusDot       = document.querySelector(".status-dot");
const apiStatusText      = document.querySelector(".status-text");

const leaderboardBody    = document.getElementById("leaderboard-body");
const leaderboardEmpty   = document.getElementById("leaderboard-empty");
const tableCount         = document.getElementById("table-count");
const leaderboardSearch  = document.getElementById("leaderboard-search");
const periodBtns         = document.querySelectorAll(".filter-btn[data-period]");

const statTotalUsers     = document.getElementById("stat-total-users");
const statTotalPRs       = document.getElementById("stat-total-prs");
const statTotalIssues    = document.getElementById("stat-total-issues");
const statTopScore       = document.getElementById("stat-top-score");

const profileInput       = document.getElementById("profile-username-input");
const profileSearchBtn   = document.getElementById("profile-search-btn");
const profileCard        = document.getElementById("profile-card");
const profileLoading     = document.getElementById("profile-loading");
const profileError       = document.getElementById("profile-error");
const profileErrorMsg    = document.getElementById("profile-error-msg");

// ── State ────────────────────────────────────────────────────────
let allRows       = [];   // Full leaderboard data
let currentPeriod = "all_time";
let sortKey       = "score";
let sortDir       = -1;   // -1 = desc, 1 = asc

// ── Navigation ───────────────────────────────────────────────────
function showView(name) {
  const isLeaderboard = name === "leaderboard";

  viewLeaderboard.classList.toggle("active", isLeaderboard);
  viewProfile.classList.toggle("active", !isLeaderboard);

  navLeaderboard.classList.toggle("active", isLeaderboard);
  navProfile.classList.toggle("active", !isLeaderboard);
}

navLeaderboard.addEventListener("click", (e) => {
  e.preventDefault();
  showView("leaderboard");
});

navProfile.addEventListener("click", (e) => {
  e.preventDefault();
  showView("profile");
});

// ── API helpers ──────────────────────────────────────────────────
async function apiFetch(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.message || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Health check ─────────────────────────────────────────────────
async function checkHealth() {
  try {
    await apiFetch("/api/health");
    apiStatusDot.className  = "status-dot online";
    apiStatusText.textContent = "API online";
  } catch {
    apiStatusDot.className  = "status-dot offline";
    apiStatusText.textContent = "API offline";
  }
}

// ── Leaderboard ──────────────────────────────────────────────────
async function loadLeaderboard(period = "all_time") {
  renderSkeletons();
  try {
    const data = await apiFetch(`/api/leaderboard?period=${period}`);
    allRows = data.leaderboard || [];
    renderTable(allRows);
    updateStats(allRows);
  } catch (err) {
    leaderboardBody.innerHTML = `
      <tr><td colspan="7" style="text-align:center;padding:32px;color:var(--color-error)">
        Failed to load leaderboard: ${err.message}
      </td></tr>`;
  }
}

function renderSkeletons() {
  leaderboardBody.innerHTML = Array(5).fill(`
    <tr class="skeleton-row">
      <td colspan="7"><div class="skeleton"></div></td>
    </tr>`).join("");
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
    const rank     = entry.rank || idx + 1;
    const rankClass = rank === 1 ? "rank-1" : rank === 2 ? "rank-2" : rank === 3 ? "rank-3" : "";
    const avatar   = entry.avatar_url || `https://github.com/${entry.username}.png?size=60`;
    const name     = entry.name || "";
    const username = entry.username || "";
    const score    = entry.total_score ?? 0;
    const prs      = entry.merged_prs ?? 0;
    const issues   = entry.issues_closed ?? 0;
    const reviews  = entry.reviews ?? 0;

    return `
      <tr>
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

function updateStats(rows) {
  statTotalUsers.textContent  = rows.length;
  statTotalPRs.textContent    = rows.reduce((s, r) => s + (r.merged_prs ?? 0), 0);
  statTotalIssues.textContent = rows.reduce((s, r) => s + (r.issues_closed ?? 0), 0);
  statTopScore.textContent    = rows.length > 0 ? (rows[0].total_score ?? 0) : 0;
}

// ── Filtering ────────────────────────────────────────────────────
leaderboardSearch.addEventListener("input", () => {
  const q = leaderboardSearch.value.trim().toLowerCase();
  const filtered = q
    ? allRows.filter(r => (r.username || "").toLowerCase().includes(q))
    : allRows;
  renderTable(filtered);
});

// ── Period filter ────────────────────────────────────────────────
periodBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    periodBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentPeriod = btn.dataset.period;
    loadLeaderboard(currentPeriod);
  });
});

// ── Profile ──────────────────────────────────────────────────────
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

  try {
    const data = await apiFetch(`/api/user/${encodeURIComponent(username)}`);

    document.getElementById("profile-avatar").src          = data.avatar_url || "";
    document.getElementById("profile-name").textContent    = data.name || data.username;
    const usernameLink = document.getElementById("profile-username-link");
    usernameLink.textContent = `@${data.username}`;
    usernameLink.href        = `https://github.com/${data.username}`;

    document.getElementById("profile-repos").textContent       = `${data.public_repos ?? 0} public repos`;
    document.getElementById("profile-total-score").textContent = data.score?.total ?? 0;
    document.getElementById("profile-prs").textContent         = data.score?.merged_prs ?? 0;
    document.getElementById("profile-issues").textContent      = data.score?.issues_closed ?? 0;
    document.getElementById("profile-reviews").textContent     = data.score?.reviews ?? 0;

    profileCard.classList.remove("hidden");
  } catch (err) {
    profileErrorMsg.textContent = err.message || "Failed to fetch user data.";
    profileError.classList.remove("hidden");
  } finally {
    profileLoading.classList.add("hidden");
    profileSearchBtn.disabled = false;
  }
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

// ── Init ─────────────────────────────────────────────────────────
(async function init() {
  await checkHealth();
  await loadLeaderboard(currentPeriod);
})();
