import { ReactNode, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Menu,
  X,
  Home,
  HardDrive,
  Monitor,
  Target,
  Activity,
  Settings,
  LogOut,
  User,
  Bell,
  Sun,
  Moon,
  Search,
  ChevronDown,
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { clsx } from 'clsx'
import { Button, Input } from './ui'

interface LayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Images', href: '/images', icon: HardDrive },
  { name: 'Machines', href: '/machines', icon: Monitor },
  { name: 'Targets', href: '/targets', icon: Target },
  { name: 'Sessions', href: '/sessions', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
  }

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    document.documentElement.classList.toggle('dark')
  }

  return (
    <div className={clsx(
      "h-screen flex overflow-hidden transition-colors duration-200",
      darkMode ? "bg-gray-900" : "bg-gray-50"
    )}>
      {/* Mobile sidebar */}
      <div className={clsx(
        'fixed inset-0 flex z-40 md:hidden',
        sidebarOpen ? 'block' : 'hidden'
      )}>
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setSidebarOpen(false)} />
        
        <div className={clsx(
          "relative flex-1 flex flex-col max-w-xs w-full transition-colors duration-200",
          darkMode ? "bg-gray-800" : "bg-white"
        )}>
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
                <span className={clsx(
                  "ml-2 text-xl font-bold",
                  darkMode ? "text-white" : "text-gray-900"
                )}>GGnet</span>
              </div>
            </div>
            
            <nav className="mt-5 px-2 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      'group flex items-center px-2 py-2 text-base font-medium rounded-lg transition-colors duration-200',
                      isActive
                        ? darkMode 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-blue-100 text-blue-900'
                        : darkMode
                          ? 'text-gray-300 hover:bg-gray-700 hover:text-white'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon
                      className={clsx(
                        'mr-4 flex-shrink-0 h-5 w-5',
                        isActive 
                          ? 'text-blue-500' 
                          : darkMode 
                            ? 'text-gray-400 group-hover:text-gray-300' 
                            : 'text-gray-400 group-hover:text-gray-500'
                      )}
                    />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64">
          <div className={clsx(
            "flex flex-col h-0 flex-1 border-r transition-colors duration-200",
            darkMode ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-white"
          )}>
            <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
              <div className="flex items-center flex-shrink-0 px-4">
                <div className="flex items-center">
                  <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">GG</span>
                  </div>
                  <span className={clsx(
                    "ml-2 text-xl font-bold",
                    darkMode ? "text-white" : "text-gray-900"
                  )}>GGnet</span>
                </div>
              </div>
              
              <nav className="mt-5 flex-1 px-2 space-y-1">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={clsx(
                        'group flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
                        isActive
                          ? darkMode 
                            ? 'bg-blue-600 text-white' 
                            : 'bg-blue-100 text-blue-900'
                          : darkMode
                            ? 'text-gray-300 hover:bg-gray-700 hover:text-white'
                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      )}
                    >
                      <item.icon
                        className={clsx(
                          'mr-3 flex-shrink-0 h-5 w-5',
                          isActive 
                            ? 'text-blue-500' 
                            : darkMode 
                              ? 'text-gray-400 group-hover:text-gray-300' 
                              : 'text-gray-400 group-hover:text-gray-500'
                        )}
                      />
                      {item.name}
                    </Link>
                  )
                })}
              </nav>
            </div>
            
            {/* User section */}
            <div className={clsx(
              "flex-shrink-0 flex border-t p-4",
              darkMode ? "border-gray-700" : "border-gray-200"
            )}>
              <div className="flex-shrink-0 w-full group block">
                <div className="flex items-center">
                  <div>
                    <div className={clsx(
                      "h-8 w-8 bg-gray-300 rounded-full flex items-center justify-center",
                      darkMode ? "bg-gray-600" : "bg-gray-300"
                    )}>
                      <User className="h-5 w-5 text-gray-600" />
                    </div>
                  </div>
                  <div className="ml-3">
                    <p className={clsx(
                      "text-sm font-medium",
                      darkMode ? "text-white" : "text-gray-700"
                    )}>
                      {user?.full_name || user?.username}
                    </p>
                    <p className={clsx(
                      "text-xs font-medium capitalize",
                      darkMode ? "text-gray-300" : "text-gray-500"
                    )}>
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
        <div className={clsx(
          "relative z-10 flex-shrink-0 flex h-16 shadow-sm border-b transition-colors duration-200",
          darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200"
        )}>
          <button
            type="button"
            className="px-4 border-r border-gray-200 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 md:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <div className="flex-1 px-4 flex justify-between">
            <div className="flex-1 flex">
              <div className="w-full flex md:ml-0">
                <div className="relative w-full text-gray-400 focus-within:text-gray-600">
                  <div className="absolute inset-y-0 left-0 flex items-center pointer-events-none">
                    <Search className="h-5 w-5" />
                  </div>
                  <input
                    className={clsx(
                      "block w-full h-full pl-8 pr-3 py-2 border-transparent rounded-md focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors duration-200",
                      darkMode 
                        ? "bg-gray-700 text-white placeholder-gray-400" 
                        : "bg-gray-50 text-gray-900 placeholder-gray-500"
                    )}
                    placeholder="Search..."
                    type="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>
            </div>
            
            <div className="ml-4 flex items-center md:ml-6">
              {/* Dark mode toggle */}
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleDarkMode}
                className="mr-2"
              >
                {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
              
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
                  <div className={clsx(
                    "origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 ring-1 ring-black ring-opacity-5 focus:outline-none transition-colors duration-200",
                    darkMode ? "bg-gray-800" : "bg-white"
                  )}>
                    <Link
                      to="/settings"
                      className={clsx(
                        "block px-4 py-2 text-sm transition-colors duration-200",
                        darkMode 
                          ? "text-gray-300 hover:bg-gray-700 hover:text-white" 
                          : "text-gray-700 hover:bg-gray-100"
                      )}
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Your Profile
                    </Link>
                    <button
                      onClick={() => {
                        handleLogout()
                        setUserMenuOpen(false)
                      }}
                      className={clsx(
                        "block w-full text-left px-4 py-2 text-sm transition-colors duration-200",
                        darkMode 
                          ? "text-gray-300 hover:bg-gray-700 hover:text-white" 
                          : "text-gray-700 hover:bg-gray-100"
                      )}
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
        <main className={clsx(
          "flex-1 relative overflow-y-auto focus:outline-none transition-colors duration-200",
          darkMode ? "bg-gray-900" : "bg-gray-50"
        )}>
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