import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Allow all hosts for live-dev mode (accessed via reverse proxy)
    allowedHosts: 'all',
  },
})
