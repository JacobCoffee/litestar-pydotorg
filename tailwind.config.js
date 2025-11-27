/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pydotorg/templates/**/*.jinja2",
    "./src/pydotorg/templates/**/*.html",
    "./resources/js/**/*.{js,ts}",
  ],
  safelist: [
    'lg:drawer-open',
    'drawer-open',
  ],
  theme: {
    extend: {
      colors: {
        python: {
          blue: {
            DEFAULT: '#3776AB',
            light: '#4B8BBE',
            dark: '#2B5B8A',
          },
          yellow: {
            DEFAULT: '#FFD43B',
            light: '#FFE873',
            dark: '#FFD700',
          },
          gray: {
            DEFAULT: '#646464',
            light: '#999999',
            dark: '#333333',
          },
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'Courier', 'monospace'],
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        python: {
          "primary": "#3776AB",
          "primary-content": "#FFFFFF",
          "secondary": "#FFD43B",
          "secondary-content": "#333333",
          "accent": "#4B8BBE",
          "accent-content": "#FFFFFF",
          "neutral": "#1D232A",
          "neutral-content": "#FFFFFF",
          "base-100": "#FFFFFF",
          "base-200": "#F5F5F5",
          "base-300": "#E5E5E5",
          "base-content": "#1F2937",
          "info": "#3ABFF8",
          "info-content": "#FFFFFF",
          "success": "#36D399",
          "success-content": "#FFFFFF",
          "warning": "#FBBD23",
          "warning-content": "#333333",
          "error": "#F87272",
          "error-content": "#FFFFFF",
        },
      },
      {
        pythondark: {
          "primary": "#4B8BBE",
          "primary-content": "#FFFFFF",
          "secondary": "#FFE873",
          "secondary-content": "#1F2937",
          "accent": "#3776AB",
          "accent-content": "#FFFFFF",
          "neutral": "#1F2937",
          "neutral-content": "#FFFFFF",
          "base-100": "#1F2937",
          "base-200": "#1A1F2E",
          "base-300": "#14161F",
          "base-content": "#E5E7EB",
          "info": "#3ABFF8",
          "info-content": "#FFFFFF",
          "success": "#36D399",
          "success-content": "#FFFFFF",
          "warning": "#FBBD23",
          "warning-content": "#1F2937",
          "error": "#F87272",
          "error-content": "#FFFFFF",
        },
      },
    ],
    darkTheme: "pythondark",
    base: true,
    styled: true,
    utils: true,
    prefix: "",
    logs: true,
    themeRoot: ":root",
  },
};
