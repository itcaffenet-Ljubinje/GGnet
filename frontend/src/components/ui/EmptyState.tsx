/**
 * EmptyState Component
 * Displayed when there's no data to show
 */

import { ReactNode } from 'react'
import { clsx } from 'clsx'
import { Button } from './Button'
import { Inbox, Search, FolderX, Database } from 'lucide-react'

export type EmptyStateIcon = 'inbox' | 'search' | 'folder' | 'database' | ReactNode

interface EmptyStateProps {
  title: string
  description?: string
  icon?: EmptyStateIcon
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

const defaultIcons = {
  inbox: Inbox,
  search: Search,
  folder: FolderX,
  database: Database
}

export function EmptyState({ 
  title, 
  description, 
  icon = 'inbox',
  action,
  className 
}: EmptyStateProps) {
  const IconComponent = typeof icon === 'string' ? defaultIcons[icon] : null
  const CustomIcon = typeof icon !== 'string' ? icon : null

  return (
    <div className={clsx(
      'flex flex-col items-center justify-center py-12 px-4 text-center',
      className
    )}>
      <div className="mb-4">
        {IconComponent && (
          <IconComponent className="h-12 w-12 text-gray-400" />
        )}
        {CustomIcon && <>{CustomIcon}</>}
      </div>
      
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
        {title}
      </h3>
      
      {description && (
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-4">
          {description}
        </p>
      )}
      
      {action && (
        <Button
          onClick={action.onClick}
          variant="primary"
          size="md"
        >
          {action.label}
        </Button>
      )}
    </div>
  )
}




