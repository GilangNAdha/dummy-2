import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // host 0.0.0.0 dan allowedHosts true supaya pratinjau lewat proxy
    // (misalnya host .e2b.app) bisa membuka aplikasi ini saat pengembangan
    host: true,
    allowedHosts: true,
  },
})
