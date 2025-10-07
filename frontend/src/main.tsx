import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
// import { BrowserRouter } from 'react-router-dom'
// import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
// import { Toaster } from 'react-hot-toast'
// import App from './App.tsx'
import App from './App.test.tsx'  // TEMPORARY: Ultra minimal test version
// import './index.css'

console.log('=== MAIN.TSX EXECUTING ===')
console.log('Root element:', document.getElementById('root'))

// Add dark class to HTML element for proper dark mode
document.documentElement.classList.add('dark')

const rootElement = document.getElementById('root')
if (!rootElement) {
  console.error('ERROR: Root element not found!')
} else {
  console.log('Root element found, creating React root...')
  
  ReactDOM.createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
  
  console.log('React root created and rendered!')
}

