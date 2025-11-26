/**
 * Admin Panel JavaScript Entry Point
 *
 * Includes SQLAdmin dependencies:
 * - jQuery for Select2 and legacy compatibility
 * - Select2 for enhanced dropdowns
 * - Flatpickr for date/time pickers
 * - HTMX for dynamic content
 * - Alpine.js for interactivity
 * - Lucide icons
 */

import $ from "jquery";
import select2 from "select2";
import flatpickr from "flatpickr";
import htmx from "htmx.org";
import Alpine from "alpinejs";
import { createIcons, icons } from "lucide";

declare global {
  interface Window {
    $: typeof $;
    jQuery: typeof $;
    htmx: typeof htmx;
    Alpine: typeof Alpine;
    flatpickr: typeof flatpickr;
  }
}

window.$ = window.jQuery = $;
window.htmx = htmx;
window.Alpine = Alpine;
window.flatpickr = flatpickr;

select2($);

htmx.config.defaultSwapStyle = "innerHTML";
htmx.config.historyCacheSize = 10;

document.body.addEventListener("htmx:beforeRequest", (event) => {
  const target = event.target as HTMLElement;
  target.classList.add("htmx-request");
});

document.body.addEventListener("htmx:afterRequest", (event) => {
  const target = event.target as HTMLElement;
  target.classList.remove("htmx-request");
});

Alpine.store("theme", {
  dark: localStorage.getItem("theme") === "pythondark",
  toggle() {
    this.dark = !this.dark;
    localStorage.setItem("theme", this.dark ? "pythondark" : "python");
    document.documentElement.setAttribute(
      "data-theme",
      this.dark ? "pythondark" : "python"
    );
  },
});

const initSelect2 = (): void => {
  $(".select2").select2({
    theme: "default",
    allowClear: true,
    placeholder: "Select...",
  });

  $(".select2-ajax").each(function () {
    const $el = $(this);
    const url = $el.data("url");
    $el.select2({
      ajax: {
        url: url,
        dataType: "json",
        delay: 250,
        data: (params: { term: string; page?: number }) => ({
          term: params.term,
          page: params.page || 1,
        }),
        processResults: (data: {
          results: unknown[];
          pagination?: unknown;
        }) => ({
          results: data.results,
          pagination: data.pagination,
        }),
      },
      minimumInputLength: 1,
      allowClear: true,
      placeholder: "Search...",
    });
  });
};

const initFlatpickr = (): void => {
  flatpickr(".flatpickr-date", { dateFormat: "Y-m-d" });
  flatpickr(".flatpickr-datetime", { dateFormat: "Y-m-d H:i", enableTime: true });
  flatpickr(".flatpickr-time", {
    dateFormat: "H:i",
    enableTime: true,
    noCalendar: true,
  });
};

const initSelectAll = (): void => {
  document.querySelectorAll<HTMLInputElement>(".select-all").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      document.querySelectorAll<HTMLInputElement>(".select-box").forEach((box) => {
        box.checked = checkbox.checked;
      });
    });
  });
};

document.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "pythondark") {
    document.documentElement.setAttribute("data-theme", "pythondark");
  }

  initSelect2();
  initFlatpickr();
  initSelectAll();
  createIcons({ icons });
  Alpine.start();

  document.body.addEventListener("htmx:afterSwap", () => {
    createIcons({ icons });
  });

  console.log("Admin panel initialized");
});
