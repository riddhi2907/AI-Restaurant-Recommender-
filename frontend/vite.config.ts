import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig(({ mode }) => {
  if (mode === "production" && !process.env.VITE_API_BASE_URL) {
    console.warn(
      "[build] VITE_API_BASE_URL is not set — production bundle will call http://localhost:8000",
    );
  }

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 5173,
    },
  };
});
