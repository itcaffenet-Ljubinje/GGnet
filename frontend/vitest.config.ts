import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    // Only include test files in src directory, explicitly exclude e2e
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/e2e/**',
      '**/e2e/**/*',
      '**/.{idea,git,cache,output,temp}/**',
      '**/playwright-report/**',
      '**/test-results/**',
      '**/*.e2e.{ts,tsx}',
      'e2e/**/*.spec.ts',
      'e2e/**/*.spec.tsx',
    ],
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
        'src/vite-env.d.ts',
        'e2e/**'
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
