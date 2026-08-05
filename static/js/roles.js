/* ============================================================
   roles.js — Role management and selection
   ============================================================ */

const ROLES = {
  student: { name: 'Student', icon: '🎓', defaultPage: 'student' },
  mentor:  { name: 'Mentor', icon: '👨‍🏫', defaultPage: 'mentor' },
  admin:   { name: 'Admin', icon: '⚙️', defaultPage: 'dashboard' },
  org:     { name: 'Organization', icon: '🏢', defaultPage: 'org' }
};

let currentRole = null;
let currentUser = null;

async function initRoles() {
  try {
    const user = await API.authMe();
    currentUser = user;
    currentRole = user.role;
    
    // Update user info in sidebar
    const nameEl = document.querySelector('.sidebar-user-name');
    const roleEl = document.getElementById('sidebar-user-role');
    const avatarEl = document.querySelector('.sidebar-user .avatar');
    
    if (nameEl) nameEl.textContent = user.name;
    if (roleEl) roleEl.textContent = ROLES[currentRole]?.name || currentRole;
    if (avatarEl) {
      avatarEl.innerHTML = `<img src="${user.avatar_url}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`;
    }
    
    applyRole(currentRole);
    
    // We only route to default page if we are at root, otherwise we might be deep linked
    if (location.hash === '' || location.hash === '#') {
      Router.navigate(ROLES[currentRole]?.defaultPage || 'dashboard');
    }
  } catch (err) {
    if (err.status === 401) {
      // Not authenticated, show login modal
      openModal('modal-auth-login');
    } else {
      console.error("Failed to check auth state:", err);
    }
  }

  // Bind logout button
  document.getElementById('role-switch-btn')?.addEventListener('click', async () => {
    try {
      await API.logout();
      window.location.reload();
    } catch (err) {
      console.error("Logout failed:", err);
    }
  });
}

function applyRole(roleKey) {
  const role = ROLES[roleKey];
  if (!role) return;

  // Show/hide navigation items based on role
  document.querySelectorAll('[data-nav-for]').forEach(el => {
    if (el.dataset.navFor.split(',').includes(roleKey) || el.dataset.navFor === 'all') {
      el.style.display = '';
    } else {
      el.style.display = 'none';
    }
  });

  // Add the role class to the body for specific CSS scoping if needed
  document.body.className = `role-${roleKey}`;
}

// Call initRoles once DOM is ready
document.addEventListener('DOMContentLoaded', initRoles);
