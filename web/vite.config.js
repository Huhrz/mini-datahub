import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 开发时把 /api 的请求转发到 FastAPI 后端(8000)，避免跨域
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
