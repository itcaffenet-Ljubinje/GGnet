import { ReactNode, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Menu,
  X,
  User,
  Bell,
  ChevronDown,
  BarChart3,
  Database,
  Monitor,
  HardDrive,
  Camera,
  Import,
  FileText,
  Download,
  Network,
  Wifi,
  Target,
  Server,
  Layers,
  Clock,
  History as HistoryIcon,
  Activity,
  Users,
  Settings,
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { clsx } from 'clsx'
import { Button } from './ui'
import { useRealTimeUpdates } from '../hooks/useRealTimeUpdates'
import Navigation from './Navigation'
import { NavigationSection } from '../types/navigation'

interface LayoutProps {
  children: ReactNode
}

// GgRock-inspired navigation structure
const navigationSections: NavigationSection[] = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    icon: BarChart3,
    href: '/dashboard',
    single: true,
  },
  {
    id: 'machines',
    name: 'Machines',
    icon: Monitor,
    items: [
      { name: 'All Machines', href: '/machines', icon: Monitor },
      { name: 'Sessions', href: '/sessions', icon: Activity },
      { name: 'Clients', href: '/clients', icon: Users },
    ],
  },
  {
    id: 'storage',
    name: 'Storage & Arrays',
    icon: Database,
    items: [
      { name: 'Arrays', href: '/storage', icon: Database },
    ],
  },
  {
    id: 'images',
    name: 'Images',
    icon: HardDrive,
    items: [
      { name: 'All Images', href: '/images', icon: HardDrive },
      { name: 'Snapshots', href: '/snapshots', icon: Camera },
      { name: 'Import/Export', href: '/image-import-export', icon: Import },
    ],
  },
  {
    id: 'writebacks',
    name: 'Writebacks',
    icon: FileText,
    href: '/writebacks',
    single: true,
  },
  {
    id: 'updates',
    name: 'Updates',
    icon: Download,
    href: '/updates',
    single: true,
  },
  {
    id: 'network',
    name: 'Network',
    icon: Network,
    items: [
      { name: 'Network Boot', href: '/network-boot', icon: Wifi },
      { name: 'Targets', href: '/targets', icon: Target },
    ],
  },
  {
    id: 'virtualization',
    name: 'Virtualization',
    icon: Server,
    items: [
      { name: 'VMs', href: '/vms', icon: Server },
    ],
  },
  {
    id: 'operations',
    name: 'Operations',
    icon: Layers,
    items: [
      { name: 'Batch Operations', href: '/batch-operations', icon: Layers },
      { name: 'Scheduler', href: '/scheduler', icon: Clock },
      { name: 'Activities', href: '/activities', icon: HistoryIcon },
    ],
  },
  {
    id: 'monitoring',
    name: 'Monitoring',
    icon: BarChart3,
    href: '/system-monitor',
    single: true,
  },
  {
    id: 'settings',
    name: 'Settings',
    icon: Settings,
    href: '/settings',
    single: true,
  },
]

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const location = useLocation()
  const { user, logout } = useAuthStore()
  
  // Initialize real-time updates
  useRealTimeUpdates()

  // Load collapsed sections from localStorage
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('ggnet-nav-collapsed')
    return saved ? new Set(JSON.parse(saved)) : new Set()
  })

  const toggleSection = (sectionId: string) => {
    setCollapsedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      localStorage.setItem('ggnet-nav-collapsed', JSON.stringify(Array.from(newSet)))
      return newSet
    })
  }

  const handleLogout = () => {
    logout()
  }

  return (
    <div className="h-screen flex overflow-hidden transition-all duration-300 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Mobile sidebar */}
      <div className={clsx(
        'fixed inset-0 flex z-40 md:hidden',
        sidebarOpen ? 'block' : 'hidden'
      )}>
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setSidebarOpen(false)} />
        
        <div className="relative flex-1 flex flex-col max-w-xs w-full transition-all duration-300 backdrop-blur-md bg-gray-800/90 border-r border-gray-700/50">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              type="button"
              className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6 text-white" />
            </button>
          </div>
          
          <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
            <div className="flex-shrink-0 flex items-center px-4">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">GG</span>
                </div>
                <span className="ml-2 text-xl font-bold text-white">GGnet</span>
              </div>
            </div>
            
            <Navigation
              sections={navigationSections}
              collapsedSections={collapsedSections}
              onToggleSection={toggleSection}
              onItemClick={() => setSidebarOpen(false)}
              isMobile={true}
            />
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64">
          <div className="flex flex-col h-0 flex-1 border-r transition-all duration-300 backdrop-blur-md border-gray-700/50 bg-gray-800/90">
            <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
              <div className="flex items-center flex-shrink-0 px-4">
                <div className="flex items-center">
                  <div className="h-8 w-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-lg">
                    <span className="text-white font-bold text-sm">GG</span>
                  </div>
                  <span className="ml-2 text-xl font-bold text-white">GGnet</span>
                </div>
              </div>
              
              {/* Navigation */}
              <Navigation
                sections={navigationSections}
                collapsedSections={collapsedSections}
                onToggleSection={toggleSection}
                isMobile={false}
              />
            </div>
            
            {/* User section */}
            <div className="flex-shrink-0 flex border-t border-gray-700 p-4">
              <div className="flex-shrink-0 w-full group block">
                <div className="flex items-center">
                  <div>
                    <div className="h-8 w-8 bg-gray-600 rounded-full flex items-center justify-center">
                      <User className="h-5 w-5 text-gray-300" />
                    </div>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-white">
                      {user?.full_name || user?.username}
                    </p>
                    <p className="text-xs font-medium capitalize text-gray-300">
                      {user?.role}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        {/* Top navigation */}
        <div className="relative z-10 flex-shrink-0 flex h-16 shadow-lg border-b border-gray-700/50 bg-gray-800/90 transition-all duration-300 backdrop-blur-md">
          <button
            type="button"
            className="px-4 border-r border-gray-200 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 md:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <div className="flex-1 px-4 flex justify-end">
            
            <div className="ml-4 flex items-center md:ml-6">
              {/* Notifications */}
              <Button
                variant="ghost"
                size="sm"
                className="mr-2 relative"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full"></span>
              </Button>
              
              {/* User menu */}
              <div className="relative">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  rightIcon={<ChevronDown className="h-4 w-4" />}
                >
                  <User className="h-4 w-4 mr-2" />
                  {user?.username}
                </Button>
                
                {userMenuOpen && (
                  <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 ring-1 ring-black ring-opacity-5 focus:outline-none transition-colors duration-200 bg-gray-800">
                    <Link
                      to="/settings"
                      className="block px-4 py-2 text-sm transition-colors duration-200 text-gray-300 hover:bg-gray-700 hover:text-white"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Your Profile
                    </Link>
                    <button
                      onClick={() => {
                        handleLogout()
                        setUserMenuOpen(false)
                      }}
                      className="block w-full text-left px-4 py-2 text-sm transition-colors duration-200 text-gray-300 hover:bg-gray-700 hover:text-white"
                    >
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none transition-colors duration-200 bg-gray-900">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}