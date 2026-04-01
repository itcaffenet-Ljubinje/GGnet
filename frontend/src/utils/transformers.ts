/**
 * Shared data transformation utilities
 * Functions to transform backend data for frontend display
 */

/**
 * Transform machine data for display
 */
export interface MachineData {
  id: number
  name: string
  description?: string
  mac_address: string
  ip_address?: string
  hostname?: string
  boot_mode: string
  secure_boot_enabled: boolean
  status: string
  is_online: boolean
  location?: string
  room?: string
  asset_tag?: string
  created_at: string
  last_seen?: string
  last_boot?: string
  boot_count: number
}

/**
 * Transform machine data for display
 * @param machine - Raw machine data from backend
 * @returns Transformed machine data
 */
export function transformMachineData(machine: any): MachineData {
  return {
    id: machine.id || 0,
    name: machine.name || 'Unnamed Machine',
    description: machine.description || '',
    mac_address: machine.mac_address || '',
    ip_address: machine.ip_address || '',
    hostname: machine.hostname || '',
    boot_mode: machine.boot_mode || 'pxe',
    secure_boot_enabled: machine.secure_boot_enabled || false,
    status: machine.status || 'inactive',
    is_online: machine.is_online || false,
    location: machine.location || '',
    room: machine.room || '',
    asset_tag: machine.asset_tag || '',
    created_at: machine.created_at || new Date().toISOString(),
    last_seen: machine.last_seen || undefined,
    last_boot: machine.last_boot || undefined,
    boot_count: machine.boot_count || 0,
  }
}

/**
 * Transform image data for display
 */
export interface ImageData {
  id?: number
  path: string
  name: string
  description?: string
  size: number
  format?: string
  created_at: string
  updated_at?: string
  is_default?: boolean
  machine_count?: number
}

/**
 * Transform image data for display
 * @param image - Raw image data from backend
 * @returns Transformed image data
 */
export function transformImageData(image: any): ImageData {
  return {
    id: image.id,
    path: image.path || '',
    name: image.name || 'Unnamed Image',
    description: image.description || '',
    size: image.size || 0,
    format: image.format || 'raw',
    created_at: image.created_at || new Date().toISOString(),
    updated_at: image.updated_at || undefined,
    is_default: image.is_default || false,
    machine_count: image.machine_count || 0,
  }
}

/**
 * Transform storage/array data for display
 */
export interface StorageData {
  pool_name?: string
  status?: string
  total_space: number
  used_space: number
  free_space: number
  reserved_space?: number
  raid_level?: string
  drives?: Array<{
    device: string
    model?: string
    serial?: string
    size: number
    status: string
    role?: string
    temperature?: number
  }>
}

/**
 * Transform storage data for display
 * @param storage - Raw storage data from backend
 * @returns Transformed storage data
 */
export function transformStorageData(storage: any): StorageData {
  return {
    pool_name: storage.pool_name || storage.name || 'default',
    status: storage.status || 'unknown',
    total_space: storage.total_space || storage.total || 0,
    used_space: storage.used_space || storage.used || 0,
    free_space: storage.free_space || storage.free || 0,
    reserved_space: storage.reserved_space || storage.reserved || 0,
    raid_level: storage.raid_level || storage.raid || undefined,
    drives: storage.drives?.map((drive: any) => ({
      device: drive.device || drive.path || '',
      model: drive.model || '',
      serial: drive.serial || '',
      size: drive.size || 0,
      status: drive.status || 'unknown',
      role: drive.role || 'data',
      temperature: drive.temperature || undefined,
    })) || [],
  }
}

/**
 * Transform VM data for display
 */
export interface VMData {
  id: number
  name: string
  description?: string
  status: string
  memory_mb?: number
  cpu_cores?: number
  disk_size_gb?: number
  created_at: string
  updated_at?: string
}

/**
 * Transform VM data for display
 * @param vm - Raw VM data from backend
 * @returns Transformed VM data
 */
export function transformVMData(vm: any): VMData {
  return {
    id: vm.id || 0,
    name: vm.name || 'Unnamed VM',
    description: vm.description || '',
    status: vm.status || 'stopped',
    memory_mb: vm.memory_mb || vm.memory || 0,
    cpu_cores: vm.cpu_cores || vm.cpus || 0,
    disk_size_gb: vm.disk_size_gb || vm.disk || 0,
    created_at: vm.created_at || new Date().toISOString(),
    updated_at: vm.updated_at || undefined,
  }
}

/**
 * Transform session data for display
 */
export interface SessionData {
  id: number
  machine_id: number
  machine_name?: string
  image_path?: string
  status: string
  started_at: string
  ended_at?: string
  duration_seconds?: number
}

/**
 * Transform session data for display
 * @param session - Raw session data from backend
 * @returns Transformed session data
 */
export function transformSessionData(session: any): SessionData {
  return {
    id: session.id || 0,
    machine_id: session.machine_id || 0,
    machine_name: session.machine_name || session.machine?.name || '',
    image_path: session.image_path || session.image?.path || '',
    status: session.status || 'unknown',
    started_at: session.started_at || new Date().toISOString(),
    ended_at: session.ended_at || undefined,
    duration_seconds: session.duration_seconds || session.duration || 0,
  }
}




