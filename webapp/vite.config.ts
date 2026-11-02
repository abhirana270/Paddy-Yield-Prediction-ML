import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the FastAPI server runs separately on :8000; on Vercel the
// frontend and /api function share one domain, so no proxy is needed there.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
});
