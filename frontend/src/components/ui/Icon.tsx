import { 
  // Common icons used across the app
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Clock,
  Database,
  Eye,
  EyeOff,
  File as FileIcon,
  Filter,
  HardDrive,
  Home,
  Info,
  Loader2,
  Monitor,
  Network,
  Plus,
  RefreshCw,
  Save,
  Search,
  Server,
  Shield,
  Target,
  TrendingDown,
  TrendingUp,
  Upload,
  User,
  Users,
  Wifi,
  WifiOff,
  X,
  Zap,
  Bell,
  Cpu,
  MemoryStick
} from 'lucide-react'

// Icon mapping for better tree shaking
export const icons = {
  activity: Activity,
  'alert-circle': AlertCircle,
  'alert-triangle': AlertTriangle,
  'arrow-left': ArrowLeft,
  'check-circle': CheckCircle,
  clock: Clock,
  database: Database,
  eye: Eye,
  'eye-off': EyeOff,
  file: FileIcon,
  filter: Filter,
  'hard-drive': HardDrive,
  home: Home,
  info: Info,
  loader: Loader2,
  monitor: Monitor,
  network: Network,
  plus: Plus,
  refresh: RefreshCw,
  save: Save,
  search: Search,
  server: Server,
  shield: Shield,
  target: Target,
  'trending-down': TrendingDown,
  'trending-up': TrendingUp,
  upload: Upload,
  user: User,
  users: Users,
  wifi: Wifi,
  'wifi-off': WifiOff,
  x: X,
  zap: Zap,
  bell: Bell,
  cpu: Cpu,
  memory: MemoryStick
} as const

export type IconName = keyof typeof icons

interface IconProps {
  name: IconName
  className?: string
  size?: number
}

export function Icon({ name, className = '', size }: IconProps) {
  const IconComponent = icons[name]
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found`)
    return null
  }
  
  return <IconComponent className={className} size={size} />
}

// Re-export commonly used icons for backward compatibility
export {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Clock,
  Database,
  Eye,
  EyeOff,
  FileIcon as File,
  Filter,
  HardDrive,
  Home,
  Info,
  Loader2,
  Monitor,
  Network,
  Plus,
  RefreshCw,
  Save,
  Search,
  Server,
  Shield,
  Target,
  TrendingDown,
  TrendingUp,
  Upload,
  User,
  Users,
  Wifi,
  WifiOff,
  X,
  Zap,
  Bell,
  Cpu,
  MemoryStick
}