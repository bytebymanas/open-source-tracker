// Main Application Entry Point

document.addEventListener('DOMContentLoaded', () => {
  
  // Register routes
  appRouter.addRoute('dashboard', renderDashboard);
  appRouter.addRoute('repositories', renderRepositories);
  appRouter.addRoute('activity', renderActivity);
  appRouter.addRoute('goals', renderGoals);
  appRouter.addRoute('leaderboards', renderLeaderboards);
  appRouter.addRoute('mentors', renderMentors);
  appRouter.addRoute('settings', renderSettings);
  appRouter.addRoute('profile', renderProfile);

  // Parse initial route from hash, or default to dashboard
  const hash = window.location.hash.replace('#', '');
  const initialPage = hash || 'dashboard';
  
  // Navigate to initial page
  appRouter.navigate(initialPage, false);
});


// Placeholder render functions (to be moved to individual page scripts later)

function renderRepositories() {
  const container = document.getElementById('repositories-content');
  container.innerHTML = '<div class="card"><p>Repositories list will go here.</p></div>';
}

function renderActivity() {
  const container = document.getElementById('activity-content');
  container.innerHTML = '<div class="card"><p>Activity feed will go here.</p></div>';
}

function renderGoals() {
  const container = document.getElementById('goals-content');
  container.innerHTML = '<div class="card"><p>Goals tracking will go here.</p></div>';
}

function renderMentors() {
  const container = document.getElementById('mentors-content');
  container.innerHTML = '<div class="card"><p>Mentor review queue will go here.</p></div>';
}

function renderSettings() {
  const container = document.getElementById('settings-content');
  container.innerHTML = '<div class="card"><p>Settings panel will go here.</p></div>';
}

function renderProfile() {
  const container = document.getElementById('profile-content');
  container.innerHTML = '<div class="card"><p>User profile will go here.</p></div>';
}
