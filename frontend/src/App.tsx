import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { NotificationProvider } from './components/notifications'

const LoginPage = lazy(() => import('./pages/LoginPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ImagesPage = lazy(() => import('./pages/ImagesPage'))
const MachinesPage = lazy(() => import('./pages/MachinesPage'))
const TargetsPage = lazy(() => import('./pages/TargetsPage'))
const SessionsPage = lazy(() => import('./pages/SessionsPage'))
const NetworkBootPage = lazy(() => import('./pages/NetworkBootPage'))
const SystemMonitorPage = lazy(() => import('./pages/SystemMonitorPage'))
const ArrayConfigurationPage = lazy(() => import('./pages/ArrayConfigurationPage'))
const MonitoringPage = lazy(() => import('./pages/MonitoringPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <NotificationProvider>
      <ErrorBoundary>
        {!isAuthenticated ? (
          <Suspense fallback={<div className="p-4 text-gray-500">Loading...</div>}>
            <LoginPage />
          </Suspense>
        ) : (
          <Layout>
            <Suspense fallback={<div className="p-4 text-gray-500">Loading...</div>}>
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
            </Suspense>
          </Layout>
        )}
      </ErrorBoundary>
    </NotificationProvider>
  )
}

export default App

