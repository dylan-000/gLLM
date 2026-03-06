import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/gllm': {
        target: 'http://localhost:8001',
        ws: true,
      },
      '/assets': {
        target: 'http://localhost:8001',
      },
      '/chainlit-auth': {
        target: 'http://localhost:8001',
      }
    },
  },
})

