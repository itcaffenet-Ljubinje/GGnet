import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/',
  resolve: {
    alias: {
      '@': resolve(new URL('./src', import.meta.url).pathname),
    },
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    assetsDir: 'assets',
    chunkSizeWarningLimit: 2000, // Increase warning limit to 2MB
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Core React libraries
          if (id.includes('react') || id.includes('react-dom')) {
            return 'react-core'
          }
          
          // React Router
          if (id.includes('react-router')) {
            return 'react-router'
          }
          
          // TanStack Query (React Query)
          if (id.includes('@tanstack/react-query') || id.includes('@tanstack/query-core')) {
            return 'react-query'
          }
          
          // Charts library
          if (id.includes('recharts')) {
            return 'charts'
          }
          
          // UI libraries
          if (id.includes('lucide-react')) {
            return 'icons'
          }
          
          // Utility libraries
          if (id.includes('axios') || id.includes('date-fns') || id.includes('clsx')) {
            return 'utils'
          }
          
          // Animation libraries
          if (id.includes('framer-motion')) {
            return 'animations'
          }
          
          // State management
          if (id.includes('zustand')) {
            return 'state'
          }
          
          // Toast notifications
          if (id.includes('react-hot-toast')) {
            return 'notifications'
          }
          
          // Node modules (vendor libraries)
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/\.(css)$/.test(assetInfo.name)) {
            return `assets/css/[name]-[hash][extname]`
          }
          if (/\.(png|jpe?g|gif|svg)$/.test(assetInfo.name)) {
            return `assets/images/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
      },
    },
  },
})

