import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In real-backend mode the frontend calls /api/*, and Vite forwards it to the
// FastAPI server. This avoids CORS problems during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
