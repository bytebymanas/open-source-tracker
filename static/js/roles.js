/* ============================================================
   roles.js — Role management and selection
   ============================================================ */

const ROLES = {
  student: { name: 'Student', icon: '🎓', defaultPage: 'student' },
  mentor:  { name: 'Mentor', icon: '👨‍🏫', defaultPage: 'mentor' },
  admin:   { name: 'Admin', icon: '⚙️', defaultPage: 'dashboard' },
  org:     { name: 'Organization', icon: '🏢', defaultPage: 'org' }
};

let currentRole = localStorage.getItem('cusoc_role');

function initRoles() {
  if (!currentRole || !ROLES[currentRole]) {
    openModal('modal-role-picker');
  } else {
    applyRole(currentRole);
  }

  // Bind role picker modal buttons
  document.querySelectorAll('.role-select-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const role = btn.dataset.role;
      if (ROLES[role]) {
        currentRole = role;
        localStorage.setItem('cusoc_role', role);
        closeModal('modal-role-picker');
        applyRole(role);
        Router.navigate(ROLES[role].defaultPage);
      }
    });
  });

  // Bind sidebar role switcher
  document.getElementById('role-switch-btn')?.addEventListener('click', () => {
    openModal('modal-role-picker');
  });
}

function applyRole(roleKey) {
  const role = ROLES[roleKey];
  if (!role) return;

  // Update sidebar user metadata
  const roleLabel = document.getElementById('sidebar-user-role');
  if (roleLabel) roleLabel.textContent = role.name;
  
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
