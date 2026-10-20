import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const epaProxy = (target, prefix) => ({
  target,
  changeOrigin: true,
  rewrite: (path) => path.replace(prefix, '') || '/',
});

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api/v1/epa/licensing": epaProxy(process.env.EPA_LICENSING_TARGET || "http://127.0.0.1:8001", "/api/v1/epa/licensing"),
      "/api/v1/epa/incidents": epaProxy(process.env.EPA_INCIDENTS_TARGET || "http://127.0.0.1:8002", "/api/v1/epa/incidents"),
      "/api": process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8000",
    },
  },
});
