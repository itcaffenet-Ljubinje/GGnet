import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useRealTimeUpdates } from './hooks/useRealTimeUpdates'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ImagesPage from './pages/ImagesPage'
import MachinesPage from './pages/MachinesPage'
import TargetsPage from './pages/TargetsPage'
import SessionsPage from './pages/SessionsPage'
import SettingsPage from './pages/SettingsPage'
import NotFoundPage from './pages/NotFoundPage'

function App() {
  const { isAuthenticated } = useAuthStore()
  
  // Initialize real-time updates when authenticated
  useRealTimeUpdates()

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <ErrorBoundary>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/images" element={<ImagesPage />} />
          <Route path="/machines" element={<MachinesPage />} />
          <Route path="/targets" element={<TargetsPage />} />
          <Route path="/sessions" element={<SessionsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Layout>
    </ErrorBoundary>
  )
}

export default App

