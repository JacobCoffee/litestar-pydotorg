import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  root: "resources",
  base: "/static/",
  publicDir: "../public",
  build: {
    outDir: "../static",
    emptyOutDir: false,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "resources/js/main.ts"),
        admin: resolve(__dirname, "resources/js/admin.ts"),
        timeline: resolve(__dirname, "resources/js/timeline.ts"),
        styles: resolve(__dirname, "resources/css/input.css"),
        "admin-styles": resolve(__dirname, "resources/css/admin.css"),
        "timeline-styles": resolve(__dirname, "resources/css/timeline.css"),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === "admin") {
            return "js/admin.js";
          }
          if (chunkInfo.name === "timeline") {
            return "js/timeline.js";
          }
          return "js/[name]-[hash].js";
        },
        chunkFileNames: "js/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === "admin-styles.css" || assetInfo.names?.includes("admin-styles.css")) {
            return "css/admin.css";
          }
          if (assetInfo.name === "timeline-styles.css" || assetInfo.names?.includes("timeline-styles.css")) {
            return "css/timeline.css";
          }
          if (assetInfo.name?.endsWith(".css")) {
            return "css/[name]-[hash][extname]";
          }
          return "assets/[name]-[hash][extname]";
        },
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    host: "0.0.0.0",
    cors: true,
    hmr: {
      host: "localhost",
    },
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "resources"),
    },
  },
});
