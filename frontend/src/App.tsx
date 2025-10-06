import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { NotificationProvider } from './components/notifications'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ImagesPage from './pages/ImagesPage'
import MachinesPage from './pages/MachinesPage'
import TargetsPage from './pages/TargetsPage'
import SessionsPage from './pages/SessionsPage'
import NetworkBootPage from './pages/NetworkBootPage'
import SystemMonitorPage from './pages/SystemMonitorPage'
import ArrayConfigurationPage from './pages/ArrayConfigurationPage'
import MonitoringPage from './pages/MonitoringPage'
import SettingsPage from './pages/SettingsPage'
import NotFoundPage from './pages/NotFoundPage'

function App() {
  const { isAuthenticated } = useAuthStore()
  
  console.log('App component rendering, isAuthenticated:', isAuthenticated)

  return (
    <NotificationProvider>
      <ErrorBoundary>
        {!isAuthenticated ? (
          <LoginPage />
        ) : (
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/images" element={<ImagesPage />} />
              <Route path="/machines" element={<MachinesPage />} />
              <Route path="/targets" element={<TargetsPage />} />
              <Route path="/sessions" element={<SessionsPage />} />
              <Route path="/network-boot" element={<NetworkBootPage />} />
              <Route path="/system-monitor" element={<SystemMonitorPage />} />
              <Route path="/storage" element={<ArrayConfigurationPage />} />
              <Route path="/monitoring" element={<MonitoringPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Layout>
        )}
      </ErrorBoundary>
    </NotificationProvider>
  )
}

export default App

