import { LucideIcon } from 'lucide-react'

export interface NavigationItem {
  name: string
  href: string
  icon: LucideIcon
  badge?: number
}

export interface NavigationSection {
  id: string
  name: string
  icon: LucideIcon
  href?: string
  items?: NavigationItem[]
  single?: boolean
  badge?: number
}

