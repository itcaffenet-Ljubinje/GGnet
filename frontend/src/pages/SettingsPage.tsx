import { useState } from 'react'
import { useQuery } from 'react-query'
import { Settings, User, Shield, Database, Network, Bell } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { apiHelpers } from '../lib/api'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile')
  const { user } = useAuthStore()

  const { data: storageData } = useQuery('storage', () => apiHelpers.getStorageInfo())
  const { data: healthData } = useQuery('health', () => apiHelpers.getDetailedHealth())

  const tabs = [
    { id: 'profile', name: 'Profile', icon: User },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'system', name: 'System', icon: Database },
    { id: 'network', name: 'Network', icon: Network },
    { id: 'notifications', name: 'Notifications', icon: Bell },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your account and system configuration
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar */}
        <div className="lg:w-64">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  activeTab === tab.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <tab.icon className="mr-3 h-5 w-5" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Profile Information</h3>
                <p className="card-description">
                  Update your account profile information
                </p>
              </div>
              <div className="card-content space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="form-group">
                    <label className="form-label">Username</label>
                    <input
                      type="text"
                      value={user?.username || ''}
                      disabled
                      className="input bg-gray-50"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Email</label>
                    <input
                      type="email"
                      value={user?.email || ''}
                      className="input"
                      placeholder="Enter your email"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input
                      type="text"
                      value={user?.full_name || ''}
                      className="input"
                      placeholder="Enter your full name"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Role</label>
                    <input
                      type="text"
                      value={user?.role || ''}
                      disabled
                      className="input bg-gray-50 capitalize"
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <button className="btn btn-primary btn-md">
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Change Password</h3>
                  <p className="card-description">
                    Update your password to keep your account secure
                  </p>
                </div>
                <div className="card-content space-y-4">
                  <div className="form-group">
                    <label className="form-label">Current Password</label>
                    <input type="password" className="input" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">New Password</label>
                    <input type="password" className="input" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Confirm New Password</label>
                    <input type="password" className="input" />
                  </div>
                  <div className="flex justify-end">
                    <button className="btn btn-primary btn-md">
                      Update Password
                    </button>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Security Settings</h3>
                </div>
                <div className="card-content space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Two-Factor Authentication</h4>
                      <p className="text-sm text-gray-500">Add an extra layer of security</p>
                    </div>
                    <button className="btn btn-secondary btn-sm">Enable</button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Session Timeout</h4>
                      <p className="text-sm text-gray-500">Automatically log out after inactivity</p>
                    </div>
                    <select className="input w-32">
                      <option>30 minutes</option>
                      <option>1 hour</option>
                      <option>4 hours</option>
                      <option>Never</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'system' && (
            <div className="space-y-6">
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">System Status</h3>
                </div>
                <div className="card-content">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">System Health</h4>
                      <p className="text-sm text-gray-500 mt-1">
                        Status: <span className={`font-medium ${
                          healthData?.data?.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {healthData?.data?.status || 'Unknown'}
                        </span>
                      </p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Storage Usage</h4>
                      <p className="text-sm text-gray-500 mt-1">
                        Images: {storageData?.data?.images_storage?.usage_percent?.toFixed(1) || 0}% used
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">System Configuration</h3>
                </div>
                <div className="card-content space-y-4">
                  <div className="form-group">
                    <label className="form-label">Default Boot Timeout</label>
                    <select className="input">
                      <option>5 seconds</option>
                      <option>10 seconds</option>
                      <option>30 seconds</option>
                      <option>60 seconds</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Max Upload Size (GB)</label>
                    <input type="number" className="input" defaultValue="10" />
                  </div>
                  <div className="flex justify-end">
                    <button className="btn btn-primary btn-md">
                      Save Configuration
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'network' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Network Configuration</h3>
              </div>
              <div className="card-content space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="form-group">
                    <label className="form-label">Server IP Address</label>
                    <input type="text" className="input" defaultValue="192.168.1.100" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">iSCSI Port</label>
                    <input type="number" className="input" defaultValue="3260" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">TFTP Root</label>
                    <input type="text" className="input" defaultValue="/var/lib/tftpboot" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">DHCP Range Start</label>
                    <input type="text" className="input" defaultValue="192.168.1.100" />
                  </div>
                </div>
                <div className="flex justify-end">
                  <button className="btn btn-primary btn-md">
                    Save Network Settings
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Notification Preferences</h3>
              </div>
              <div className="card-content space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Email Notifications</h4>
                      <p className="text-sm text-gray-500">Receive email alerts for system events</p>
                    </div>
                    <input type="checkbox" className="h-4 w-4 text-primary-600" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Session Alerts</h4>
                      <p className="text-sm text-gray-500">Get notified when sessions start/stop</p>
                    </div>
                    <input type="checkbox" className="h-4 w-4 text-primary-600" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">System Health Alerts</h4>
                      <p className="text-sm text-gray-500">Receive alerts for system health issues</p>
                    </div>
                    <input type="checkbox" className="h-4 w-4 text-primary-600" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Storage Warnings</h4>
                      <p className="text-sm text-gray-500">Get notified when storage is running low</p>
                    </div>
                    <input type="checkbox" className="h-4 w-4 text-primary-600" defaultChecked />
                  </div>
                </div>
                <div className="flex justify-end">
                  <button className="btn btn-primary btn-md">
                    Save Preferences
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

