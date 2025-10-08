/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    // Output directory
    outDir: 'dist',
    // Generate sourcemaps for production debugging (optional, remove if not needed)
    sourcemap: false,
    // Target modern browsers for smaller bundle
    target: 'es2015',
    // Minification options
    minify: 'esbuild',
    // Chunk size warning limit (in kB)
    chunkSizeWarningLimit: 1000,
    // Rollup options for advanced optimizations
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: (id) => {
          // Vendor chunks
          if (id.includes('node_modules')) {
            // React and related libraries
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
              return 'vendor-react'
            }
            // Chart libraries (recharts is large)
            if (id.includes('recharts')) {
              return 'vendor-charts'
            }
            // Tanstack Query
            if (id.includes('@tanstack/react-query')) {
              return 'vendor-query'
            }
            // Icons
            if (id.includes('lucide-react')) {
              return 'vendor-icons'
            }
            // Form libraries
            if (id.includes('react-hook-form') || id.includes('react-dropzone')) {
              return 'vendor-forms'
            }
            // Other vendor code
            return 'vendor-misc'
          }
        },
        // Naming patterns for chunks
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          // Organize assets by type
          const info = assetInfo.name?.split('.') || []
          const ext = info[info.length - 1]
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `assets/images/[name]-[hash][extname]`
          }
          if (/woff|woff2|eot|ttf|otf/i.test(ext)) {
            return `assets/fonts/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        }
      }
    },
    // CSS code splitting
    cssCodeSplit: true,
    // Optimize dependencies
    commonjsOptions: {
      transformMixedEsModules: true
    }
  },
  // Optimize dependencies pre-bundling
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'axios',
      'zustand'
    ],
    exclude: ['@testing-library/react', '@testing-library/user-event', 'vitest']
  },
  server: {
    port: 3000,
    host: '127.0.0.1',
    strictPort: true,
    hmr: {
      protocol: 'ws',
      host: '127.0.0.1',
      port: 3000,
      clientPort: 3000,
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        bypass: (req, res, options) => {
          // Don't proxy if it's a Vite internal request
          if (req.url?.startsWith('/@')) {
            return req.url
          }
        },
      }
    }
  },
  // Enable esbuild optimizations
  esbuild: {
    // Remove console.log in production
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : [],
    // Optimize for modern syntax
    target: 'es2015',
    legalComments: 'none'
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.d.ts',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'src/test/**',
        'src/main.tsx',
        'src/vite-env.d.ts'
      ]
    }
  }
})