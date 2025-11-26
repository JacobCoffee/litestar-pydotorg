/**
 * Python.org - Main JavaScript Entry Point
 *
 * Uses:
 * - HTMX for dynamic content loading
 * - Alpine.js for lightweight interactivity
 * - DaisyUI/Tailwind for styling
 */

import htmx from "htmx.org";
import Alpine from "alpinejs";

// Make HTMX available globally
declare global {
  interface Window {
    htmx: typeof htmx;
    Alpine: typeof Alpine;
  }
}

window.htmx = htmx;
window.Alpine = Alpine;

// Configure HTMX
htmx.config.defaultSwapStyle = "innerHTML";
htmx.config.historyCacheSize = 10;
htmx.config.refreshOnHistoryMiss = true;

// HTMX event handlers for loading states
document.body.addEventListener("htmx:beforeRequest", (event) => {
  const target = event.target as HTMLElement;
  target.classList.add("htmx-request");
});

document.body.addEventListener("htmx:afterRequest", (event) => {
  const target = event.target as HTMLElement;
  target.classList.remove("htmx-request");
});

// Handle HTMX errors
document.body.addEventListener("htmx:responseError", (event) => {
  console.error("HTMX request failed:", event);
});

// Theme management
const initTheme = (): void => {
  const theme = localStorage.getItem("theme") || "python";
  document.documentElement.setAttribute("data-theme", theme);
};

const toggleTheme = (): void => {
  const currentTheme = document.documentElement.getAttribute("data-theme");
  const newTheme = currentTheme === "python" ? "dark" : "python";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);
};

// Scroll to top button
const initScrollToTop = (): void => {
  const scrollBtn = document.getElementById("scroll-to-top");
  if (!scrollBtn) return;

  window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
      scrollBtn.classList.remove("hidden");
    } else {
      scrollBtn.classList.add("hidden");
    }
  });

  scrollBtn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
};

// Mobile menu toggle
const initMobileMenu = (): void => {
  const menuToggle = document.getElementById("mobile-menu-toggle");
  const mobileMenu = document.getElementById("mobile-menu");

  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener("click", () => {
      mobileMenu.classList.toggle("hidden");
    });
  }
};

// Initialize Alpine.js components
Alpine.data("dropdown", () => ({
  open: false,
  toggle() {
    this.open = !this.open;
  },
  close() {
    this.open = false;
  },
}));

Alpine.data("modal", () => ({
  open: false,
  show() {
    this.open = true;
  },
  hide() {
    this.open = false;
  },
}));

Alpine.data("tabs", () => ({
  activeTab: 0,
  setActive(index: number) {
    this.activeTab = index;
  },
  isActive(index: number) {
    return this.activeTab === index;
  },
}));

Alpine.data("toast", () => ({
  toasts: [] as Array<{ id: number; message: string; type: string }>,
  add(message: string, type = "info") {
    const id = Date.now();
    this.toasts.push({ id, message, type });
    setTimeout(() => this.remove(id), 5000);
  },
  remove(id: number) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
  },
}));

// Export for global access
window.toggleTheme = toggleTheme;

declare global {
  interface Window {
    toggleTheme: typeof toggleTheme;
  }
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initScrollToTop();
  initMobileMenu();

  // Start Alpine.js
  Alpine.start();

  console.log("Python.org frontend initialized");
});
