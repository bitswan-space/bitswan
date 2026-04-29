import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `BITSWAN_GITOPS_DOMAIN` is exported by the live-dev container's entrypoint
// and is consumed here for the dev server's `allowedHosts` list. In production
// the build doesn't run a server so the value is unused.
const gitopsDomain = process.env.BITSWAN_GITOPS_DOMAIN

export default defineConfig({
  plugins: [react()],
  // Vite's pre-bundle cache lives in tmpfs so the read-only source mount
  // doesn't have to host it (the default `<root>/node_modules/.vite` would
  // resolve through the `node_modules` symlink to /deps and work too, but
  // pinning the cache to /tmp keeps it explicit).
  cacheDir: '/tmp/.vite',
  server: {
    host: '0.0.0.0',
    port: 8080,
    allowedHosts: gitopsDomain ? ['.' + gitopsDomain] : [],
  },
})
