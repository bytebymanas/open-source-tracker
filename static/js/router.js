// Simple SPA Router

class Router {
  constructor() {
    this.routes = {};
    this.currentRoute = null;
    this.initSidebarNavigation();
    
    // Handle browser back/forward
    window.addEventListener('popstate', (e) => {
      if (e.state && e.state.page) {
        this.navigate(e.state.page, false);
      }
    });
  }

  addRoute(name, callback) {
    this.routes[name] = callback;
  }

  navigate(pageName, pushState = true) {
    if (!this.routes[pageName]) {
      console.warn(`Route ${pageName} not found.`);
      return;
    }

    // Hide all pages
    document.querySelectorAll('.page-view').forEach(page => {
      page.classList.remove('active');
    });

    // Show target page
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
      targetPage.classList.add('active');
    }

    // Update sidebar UI
    document.querySelectorAll('.sidebar-nav .nav-item, .sidebar-footer .nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.page === pageName);
    });

    // Update breadcrumb
    const breadcrumbActive = document.querySelector('.breadcrumb-active');
    if (breadcrumbActive) {
      // Capitalize first letter
      breadcrumbActive.textContent = pageName.charAt(0).toUpperCase() + pageName.slice(1);
    }

    if (pushState) {
      window.history.pushState({ page: pageName }, '', `/#${pageName}`);
    }

    this.currentRoute = pageName;
    
    // Execute route callback
    this.routes[pageName]();
  }

  initSidebarNavigation() {
    document.addEventListener('click', (e) => {
      const navItem = e.target.closest('.nav-item');
      if (navItem && navItem.dataset.page) {
        e.preventDefault();
        this.navigate(navItem.dataset.page);
      }
    });
  }
}

const appRouter = new Router();
