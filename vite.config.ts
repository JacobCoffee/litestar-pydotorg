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
        styles: resolve(__dirname, "resources/css/input.css"),
      },
      output: {
        entryFileNames: "js/[name]-[hash].js",
        chunkFileNames: "js/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
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
