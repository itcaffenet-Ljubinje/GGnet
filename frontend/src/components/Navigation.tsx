import { Link, useLocation } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { useQuery } from '@tanstack/react-query'
import { NavigationSection, NavigationItem } from '../types/navigation'
import { apiHelpers } from '../lib/api'

interface NavigationProps {
  sections: NavigationSection[]
  collapsedSections: Set<string>
  onToggleSection: (sectionId: string) => void
  onItemClick?: () => void
  isMobile?: boolean
}

export default function Navigation({
  sections,
  collapsedSections,
  onToggleSection,
  onItemClick,
  isMobile = false,
}: NavigationProps) {
  const location = useLocation()

  // Fetch active sessions count
  const { data: sessionsData } = useQuery({
    queryKey: ['sessions', 'active'],
    queryFn: async () => {
      try {
        const response = await apiHelpers.getActiveSessionsDetailed()
        return Array.isArray(response) ? response : response?.data || []
      } catch {
        return []
      }
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  // Fetch machines count (filter active ones)
  const { data: machinesData } = useQuery({
    queryKey: ['machines'],
    queryFn: async () => {
      try {
        const response = await apiHelpers.getMachines()
        const machines = Array.isArray(response) ? response : response?.data || []
        return machines.filter((m: { is_online?: boolean }) => m.is_online)
      } catch {
        return []
      }
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const activeSessionsCount = Array.isArray(sessionsData) ? sessionsData.length : 0
  const activeMachinesCount = Array.isArray(machinesData) ? machinesData.length : 0

  const isActive = (href: string) => location.pathname === href

  const isSectionActive = (section: NavigationSection) => {
    if (section.single && section.href) {
      return isActive(section.href)
    }
    if (section.items) {
      return section.items.some(item => isActive(item.href))
    }
    return false
  }

  const isSectionCollapsed = (sectionId: string) => collapsedSections.has(sectionId)

  const getBadgeCount = (section: NavigationSection, item?: NavigationItem) => {
    if (item?.href === '/sessions') {
      return activeSessionsCount > 0 ? activeSessionsCount : undefined
    }
    if (item?.href === '/machines' || section.id === 'machines') {
      return activeMachinesCount > 0 ? activeMachinesCount : undefined
    }
    return section.badge || item?.badge
  }

  const baseNavClasses = isMobile
    ? 'mt-5 px-2 space-y-1'
    : 'mt-8 px-2 space-y-1'

  const baseItemClasses = isMobile
    ? 'group flex items-center px-2 py-2 text-base font-medium rounded-lg transition-colors duration-200'
    : 'group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200'

  const baseSubItemClasses = isMobile
    ? 'group flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors duration-200'
    : 'group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200'

  return (
    <nav className={baseNavClasses}>
      {sections.map((section) => {
        const sectionActive = isSectionActive(section)
        const collapsed = isSectionCollapsed(section.id)
        
        if (section.single && section.href) {
          const itemActive = isActive(section.href)
          return (
            <Link
              key={section.id}
              to={section.href}
              className={clsx(
                baseItemClasses,
                itemActive
                  ? 'bg-blue-600 text-white shadow-lg' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              )}
              onClick={onItemClick}
            >
              <section.icon
                className={clsx(
                  isMobile ? 'mr-4' : 'mr-3',
                  'flex-shrink-0 h-5 w-5 transition-colors duration-200',
                  itemActive 
                    ? 'text-blue-200' 
                    : 'text-gray-400 group-hover:text-gray-300'
                )}
              />
              <span className="flex-1">{section.name}</span>
              {getBadgeCount(section) !== undefined && (
                <span className="ml-2 px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-600 text-white">
                  {getBadgeCount(section)}
                </span>
              )}
            </Link>
          )
        }
        
        const sectionBadge = getBadgeCount(section)
        
        return (
          <div key={section.id} className="space-y-1">
            <button
              onClick={() => onToggleSection(section.id)}
              className={clsx(
                'w-full group flex items-center justify-between',
                baseItemClasses,
                sectionActive
                  ? 'text-blue-400' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              )}
            >
              <div className="flex items-center flex-1">
                <section.icon
                  className={clsx(
                    isMobile ? 'mr-4' : 'mr-3',
                    'flex-shrink-0 h-5 w-5 transition-colors duration-200',
                    sectionActive 
                      ? 'text-blue-400' 
                      : 'text-gray-400 group-hover:text-gray-300'
                  )}
                />
                {section.name}
                {sectionBadge !== undefined && (
                  <span className="ml-2 px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-600 text-white">
                    {sectionBadge}
                  </span>
                )}
              </div>
              <ChevronRight
                className={clsx(
                  'h-4 w-4 transition-transform duration-200 flex-shrink-0',
                  collapsed ? '' : 'rotate-90'
                )}
              />
            </button>
            {!collapsed && section.items && (
              <div className={clsx('space-y-1', isMobile ? 'ml-4' : 'ml-4')}>
                {section.items.map((item) => {
                  const itemActive = isActive(item.href)
                  return (
                    <Link
                      key={item.href}
                      to={item.href}
                      className={clsx(
                        baseSubItemClasses,
                        itemActive
                          ? 'bg-blue-600 text-white shadow-lg' 
                          : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                      )}
                      onClick={onItemClick}
                    >
                      <item.icon
                        className={clsx(
                          isMobile ? 'mr-3' : 'mr-3',
                          'flex-shrink-0 h-4 w-4 transition-colors duration-200',
                          itemActive 
                            ? 'text-blue-200' 
                            : 'text-gray-500 group-hover:text-gray-300'
                        )}
                      />
                      <span className="flex-1">{item.name}</span>
                      {getBadgeCount(section, item) !== undefined && (
                        <span className="ml-2 px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-600 text-white">
                          {getBadgeCount(section, item)}
                        </span>
                      )}
                    </Link>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )
}

