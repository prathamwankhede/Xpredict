import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  optimizeDeps: {
    // Prevents Vite from scanning the entire project tree for deps on startup,
    // which hangs when the project is inside an iCloud-synced Documents folder.
    noDiscovery: true,
    include: [],
  },
  server: {
    watch: {
      // Ignore node_modules (including the .nosync symlink variant) to prevent
      // Tailwind's Oxide watcher from looping on CSS changes in node_modules.
      ignored: ['**/node_modules/**', '**/node_modules.nosync/**'],
    },
  },
})
