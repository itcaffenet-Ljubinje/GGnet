import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, ProgressBar, StatusBadge, Button } from '../components/ui'
import { 
  HardDrive, 
  Plus, 
  Settings, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  Info,
  Trash2,
  Edit,
  Shield,
  Zap,
  Database,
  Layers,
  Activity,
  RefreshCw,
  Save,
  X
} from 'lucide-react'
import { clsx } from 'clsx'
import { useNotifications } from '../components/notifications'

interface Disk {
  id: string
  path: string
  serial: string
  model: string
  size: string
  used: string
  available: string
  reserved: string
  trimStatus: 'Supported' | 'Unsupported' | 'Trimmed'
  status: 'active' | 'warning' | 'error'
}

interface Stripe {
  id: string
  name: string
  type: string
  totalSize: string
  diskCount: number
  disks: Disk[]
  selected: boolean
}

interface ArrayStats {
  totalSize: string
  usedSpace: string
  availableSpace: string
  reservedSpace: string
  reservedPercentage: number
  status: string
  timestamp: string
}

interface RaidConfig {
  id: string
  name: string
  type: 'RAID 0' | 'RAID 1' | 'RAID 5' | 'RAID 6' | 'RAID 10'
  description: string
  minDisks: number
  maxDisks: number
  capacity: string
  redundancy: string
  performance: string
  icon: React.ReactNode
  color: string
}

const raidConfigs: RaidConfig[] = [
  {
    id: 'raid0',
    name: 'RAID 0',
    type: 'RAID 0',
    description: 'Striping without parity - Maximum performance and capacity',
    minDisks: 2,
    maxDisks: 32,
    capacity: '100%',
    redundancy: 'None',
    performance: 'Excellent',
    icon: <Zap className="h-5 w-5" />,
    color: 'text-orange-500'
  },
  {
    id: 'raid1',
    name: 'RAID 1',
    type: 'RAID 1',
    description: 'Mirroring - High redundancy with good performance',
    minDisks: 2,
    maxDisks: 2,
    capacity: '50%',
    redundancy: '1 disk',
    performance: 'Good',
    icon: <Shield className="h-5 w-5" />,
    color: 'text-green-500'
  },
  {
    id: 'raid5',
    name: 'RAID 5',
    type: 'RAID 5',
    description: 'Striping with parity - Balanced performance and redundancy',
    minDisks: 3,
    maxDisks: 32,
    capacity: '67-94%',
    redundancy: '1 disk',
    performance: 'Good',
    icon: <Database className="h-5 w-5" />,
    color: 'text-blue-500'
  },
  {
    id: 'raid6',
    name: 'RAID 6',
    type: 'RAID 6',
    description: 'Striping with double parity - High redundancy',
    minDisks: 4,
    maxDisks: 32,
    capacity: '50-88%',
    redundancy: '2 disks',
    performance: 'Fair',
    icon: <Layers className="h-5 w-5" />,
    color: 'text-purple-500'
  },
  {
    id: 'raid10',
    name: 'RAID 10',
    type: 'RAID 10',
    description: 'Mirrored stripes - Best performance and redundancy',
    minDisks: 4,
    maxDisks: 32,
    capacity: '50%',
    redundancy: 'Multiple disks',
    performance: 'Excellent',
    icon: <Activity className="h-5 w-5" />,
    color: 'text-red-500'
  }
]

const mockArrayStats: ArrayStats = {
  totalSize: "39.8 GB",
  usedSpace: "22.1 GB",
  availableSpace: "17.7 GB",
  reservedSpace: "7.2 GB",
  reservedPercentage: 18.0,
  status: "A4.9.6",
  timestamp: "2025-01-05 14:30:25"
}

const mockDisks: Disk[] = [
  {
    id: '1',
    path: '/dev/sda',
    serial: 'WD-WMC5D1234567',
    model: 'WDC WD40EFRX-68N32N0',
    size: '4.0 TB',
    used: '2.1 TB',
    available: '1.9 TB',
    reserved: '500 GB',
    trimStatus: 'Supported',
    status: 'active'
  },
  {
    id: '2',
    path: '/dev/sdb',
    serial: 'WD-WMC5D1234568',
    model: 'WDC WD40EFRX-68N32N0',
    size: '4.0 TB',
    used: '2.0 TB',
    available: '2.0 TB',
    reserved: '500 GB',
    trimStatus: 'Supported',
    status: 'active'
  },
  {
    id: '3',
    path: '/dev/sdc',
    serial: 'ST4000DM005-2DP166',
    model: 'Seagate ST4000DM005',
    size: '4.0 TB',
    used: '2.2 TB',
    available: '1.8 TB',
    reserved: '500 GB',
    trimStatus: 'Trimmed',
    status: 'warning'
  },
  {
    id: '4',
    path: '/dev/sdd',
    serial: 'ST4000DM005-2DP167',
    model: 'Seagate ST4000DM005',
    size: '4.0 TB',
    used: '1.9 TB',
    available: '2.1 TB',
    reserved: '500 GB',
    trimStatus: 'Unsupported',
    status: 'error'
  }
]

const mockStripes: Stripe[] = [
  {
    id: '1',
    name: 'Stripe 1 (Single-Drive)',
    type: 'RAID 0',
    totalSize: '4.0 TB',
    diskCount: 1,
    disks: [mockDisks[0]],
    selected: false
  },
  {
    id: '2',
    name: 'Stripe 2 (Mirror)',
    type: 'RAID 1',
    totalSize: '4.0 TB',
    diskCount: 2,
    disks: [mockDisks[1], mockDisks[2]],
    selected: false
  },
  {
    id: '3',
    name: 'Stripe 3 (Single-Drive)',
    type: 'RAID 0',
    totalSize: '4.0 TB',
    diskCount: 1,
    disks: [mockDisks[3]],
    selected: false
  }
]

export default function ArrayConfigurationPage() {
  const [arrayStats, setArrayStats] = useState<ArrayStats>(mockArrayStats)
  const [disks, setDisks] = useState<Disk[]>(mockDisks)
  const [stripes, setStripes] = useState<Stripe[]>(mockStripes)
  const [showAddStripe, setShowAddStripe] = useState(false)
  const [showReservedSettings, setShowReservedSettings] = useState(false)
  const [showRaidConfig, setShowRaidConfig] = useState(false)
  const [selectedRaidType, setSelectedRaidType] = useState<string>('')
  const [selectedDisks, setSelectedDisks] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  
  const { addNotification } = useNotifications()


  const handleStripeSelect = (stripeId: string) => {
    setStripes(stripes.map(stripe => 
      stripe.id === stripeId 
        ? { ...stripe, selected: !stripe.selected }
        : stripe
    ))
  }

  const handleDeleteStripe = (stripeId: string) => {
    setStripes(stripes.filter(stripe => stripe.id !== stripeId))
  }

  const handleAddStripe = () => {
    const newStripe: Stripe = {
      id: (stripes.length + 1).toString(),
      name: `Stripe ${stripes.length + 1} (New)`,
      type: 'RAID 0',
      totalSize: '0 GB',
      diskCount: 0,
      disks: [],
      selected: false
    }
    setStripes([...stripes, newStripe])
    setShowAddStripe(false)
  }

  const handleDiskSelect = (diskId: string) => {
    setSelectedDisks(prev => 
      prev.includes(diskId) 
        ? prev.filter(id => id !== diskId)
        : [...prev, diskId]
    )
  }

  const handleCreateRaid = async () => {
    if (!selectedRaidType || selectedDisks.length === 0) {
      addNotification({
        type: 'error',
        message: 'Please select RAID type and at least one disk'
      })
      return
    }

    const raidConfig = raidConfigs.find(r => r.id === selectedRaidType)
    if (!raidConfig) return

    if (selectedDisks.length < raidConfig.minDisks) {
      addNotification({
        type: 'error',
        message: `${raidConfig.name} requires at least ${raidConfig.minDisks} disks`
      })
      return
    }

    setIsLoading(true)
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const selectedDiskObjects = disks.filter(disk => selectedDisks.includes(disk.id))
      const newStripe: Stripe = {
        id: (stripes.length + 1).toString(),
        name: `${raidConfig.name} Array ${stripes.length + 1}`,
        type: raidConfig.type,
        totalSize: `${selectedDiskObjects.length * 4} TB`, // Mock calculation
        diskCount: selectedDiskObjects.length,
        disks: selectedDiskObjects,
        selected: false
      }
      
      setStripes([...stripes, newStripe])
      setShowRaidConfig(false)
      setSelectedRaidType('')
      setSelectedDisks([])
      
      addNotification({
        type: 'success',
        message: `${raidConfig.name} array created successfully`
      })
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to create RAID array'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleRefreshDisks = async () => {
    setIsLoading(true)
    try {
      // Simulate API call to refresh disk list
      await new Promise(resolve => setTimeout(resolve, 1000))
      addNotification({
        type: 'success',
        message: 'Disk list refreshed successfully'
      })
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to refresh disk list'
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Storage Management
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Manage your disk array configuration, storage usage, and disk operations.
            </p>
          </div>
          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={handleRefreshDisks}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh Disks
            </Button>
            <Button onClick={() => setShowRaidConfig(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create RAID Array
            </Button>
          </div>
        </div>
      </div>

      {/* Main Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5" />
            Storage Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Size Information */}
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Total Size
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {arrayStats.totalSize}
              </div>
            </div>

            {/* Reserved Space */}
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Reserved Space
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {arrayStats.reservedSpace}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                ({arrayStats.reservedPercentage}%)
              </div>
            </div>

            {/* Status */}
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Status
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div className="text-2xl font-bold text-green-600">
                  {arrayStats.status}
                </div>
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {arrayStats.timestamp}
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-6">
            <ProgressBar
              value={parseFloat(arrayStats.usedSpace)}
              max={parseFloat(arrayStats.totalSize)}
              showLabel={true}
              label={`Storage Usage (${arrayStats.usedSpace} / ${arrayStats.totalSize})`}
              color="blue"
              size="md"
            />
          </div>
        </CardContent>
      </Card>

      {/* RAID Configuration Options */}
      <Card>
        <CardHeader>
          <CardTitle>RAID Configuration Options</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {raidConfigs.map((raid) => (
              <div
                key={raid.id}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => {
                  setSelectedRaidType(raid.id)
                  setShowRaidConfig(true)
                }}
              >
                <div className="flex items-center space-x-3 mb-3">
                  <div className={raid.color}>
                    {raid.icon}
                  </div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                    {raid.name}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {raid.description}
                </p>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Capacity:</span>
                    <span className="font-medium">{raid.capacity}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Redundancy:</span>
                    <span className="font-medium">{raid.redundancy}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Performance:</span>
                    <span className="font-medium">{raid.performance}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Disks:</span>
                    <span className="font-medium">{raid.minDisks}-{raid.maxDisks}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Disk Array Structure */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Disk Array Structure</CardTitle>
            <div className="flex gap-2">
              <button
                onClick={() => setShowAddStripe(true)}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Array
              </button>
              <button
                onClick={() => setShowReservedSettings(true)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Settings className="h-4 w-4 mr-1" />
                Reserved Settings
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stripes.map((stripe) => (
              <div
                key={stripe.id}
                className={clsx(
                  "border rounded-lg p-4 transition-all duration-200",
                  stripe.selected
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={stripe.selected}
                      onChange={() => handleStripeSelect(stripe.id)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">
                        {stripe.name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {stripe.type} • {stripe.totalSize} • {stripe.diskCount} disk{stripe.diskCount !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteStripe(stripe.id)}
                      className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Disk Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Available Disks</CardTitle>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {selectedDisks.length} disk{selectedDisks.length !== 1 ? 's' : ''} selected
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    SELECT
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    PATH
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    SERIAL
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    MODEL
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    SIZE
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    USED / AVAILABLE
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    RESERVED
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    TRIM STATUS
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {disks.map((disk) => (
                  <tr 
                    key={disk.id} 
                    className={clsx(
                      "hover:bg-gray-50 dark:hover:bg-gray-700",
                      selectedDisks.includes(disk.id) && "bg-blue-50 dark:bg-blue-900/20"
                    )}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedDisks.includes(disk.id)}
                        onChange={() => handleDiskSelect(disk.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                      {disk.path}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {disk.serial}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {disk.model}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {disk.size}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <div className="flex flex-col">
                        <span className="text-red-600 dark:text-red-400">{disk.used}</span>
                        <span className="text-green-600 dark:text-green-400">{disk.available}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {disk.reserved}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge
                        status={
                          disk.trimStatus === 'Supported' ? 'success' :
                          disk.trimStatus === 'Trimmed' ? 'info' :
                          disk.trimStatus === 'Unsupported' ? 'error' : 'warning'
                        }
                        text={disk.trimStatus}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Add Stripe Modal */}
      {showAddStripe && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                Add New Array
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Array Name
                  </label>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                    placeholder="Array 4 (New)"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    RAID Type
                  </label>
                  <select className="mt-1 block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100">
                    <option>RAID 0</option>
                    <option>RAID 1</option>
                    <option>RAID 5</option>
                    <option>RAID 6</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowAddStripe(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddStripe}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Add Array
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reserved Settings Modal */}
      {showReservedSettings && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                Reserved Disk Settings
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Reserved Space (GB)
                  </label>
                  <input
                    type="number"
                    className="mt-1 block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                    placeholder="500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Reserved Percentage
                  </label>
                  <input
                    type="number"
                    className="mt-1 block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                    placeholder="18"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowReservedSettings(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  Cancel
                </button>
                <button
                  onClick={() => setShowReservedSettings(false)}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Save Settings
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* RAID Configuration Modal */}
      {showRaidConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Create RAID Array</CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowRaidConfig(false)
                    setSelectedRaidType('')
                    setSelectedDisks([])
                  }}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* RAID Type Selection */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                    Select RAID Type
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {raidConfigs.map((raid) => (
                      <div
                        key={raid.id}
                        className={clsx(
                          "border rounded-lg p-4 cursor-pointer transition-all",
                          selectedRaidType === raid.id
                            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                            : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                        )}
                        onClick={() => setSelectedRaidType(raid.id)}
                      >
                        <div className="flex items-center space-x-3 mb-2">
                          <div className={raid.color}>
                            {raid.icon}
                          </div>
                          <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                            {raid.name}
                          </h4>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                          {raid.description}
                        </p>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Capacity:</span>
                            <span className="font-medium">{raid.capacity}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Redundancy:</span>
                            <span className="font-medium">{raid.redundancy}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Performance:</span>
                            <span className="font-medium">{raid.performance}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Min Disks:</span>
                            <span className="font-medium">{raid.minDisks}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Disk Selection */}
                {selectedRaidType && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                      Select Disks
                    </h3>
                    <div className="border rounded-lg overflow-hidden">
                      <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b">
                        <div className="grid grid-cols-6 gap-4 text-sm font-medium text-gray-500 dark:text-gray-300">
                          <div>Select</div>
                          <div>Path</div>
                          <div>Model</div>
                          <div>Size</div>
                          <div>Status</div>
                          <div>Trim</div>
                        </div>
                      </div>
                      <div className="max-h-64 overflow-y-auto">
                        {disks.map((disk) => (
                          <div
                            key={disk.id}
                            className={clsx(
                              "grid grid-cols-6 gap-4 px-4 py-2 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800",
                              selectedDisks.includes(disk.id) && "bg-blue-50 dark:bg-blue-900/20"
                            )}
                          >
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={selectedDisks.includes(disk.id)}
                                onChange={() => handleDiskSelect(disk.id)}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                              />
                            </div>
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                              {disk.path}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                              {disk.model}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {disk.size}
                            </div>
                            <div className="flex items-center">
                              <StatusBadge
                                status={
                                  disk.status === 'active' ? 'success' :
                                  disk.status === 'warning' ? 'warning' : 'error'
                                }
                                text={disk.status}
                              />
                            </div>
                            <div className="flex items-center">
                              <StatusBadge
                                status={
                                  disk.trimStatus === 'Supported' ? 'success' :
                                  disk.trimStatus === 'Trimmed' ? 'info' : 'error'
                                }
                                text={disk.trimStatus}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    {selectedRaidType && (
                      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <div className="text-sm text-blue-800 dark:text-blue-200">
                          <strong>Selected:</strong> {selectedDisks.length} disk{selectedDisks.length !== 1 ? 's' : ''}
                          {selectedRaidType && (
                            <>
                              <br />
                              <strong>RAID Type:</strong> {raidConfigs.find(r => r.id === selectedRaidType)?.name}
                              <br />
                              <strong>Minimum Required:</strong> {raidConfigs.find(r => r.id === selectedRaidType)?.minDisks} disk{raidConfigs.find(r => r.id === selectedRaidType)?.minDisks !== 1 ? 's' : ''}
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowRaidConfig(false)
                      setSelectedRaidType('')
                      setSelectedDisks([])
                    }}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateRaid}
                    disabled={!selectedRaidType || selectedDisks.length === 0 || isLoading}
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Create RAID Array
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
