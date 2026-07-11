import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' keeps asset paths relative so the build works whether it is served
// from a domain root or a subfolder (e.g. jnandy9.github.io/billing-app/).
export default defineConfig({
  plugins: [react()],
  base: './',
  server: { port: 5173 },
})
