/**
 * ErrorState Component
 * Displayed when there's an error loading data
 */

import { ReactNode } from 'react'
import { clsx } from 'clsx'
import { Button } from './Button'
import { AlertTriangle, RefreshCw, XCircle } from 'lucide-react'

export type ErrorStateIcon = 'alert' | 'error' | 'warning' | ReactNode

interface ErrorStateProps {
  title?: string
  message?: string
  error?: Error | string
  icon?: ErrorStateIcon
  onRetry?: () => void
  retryLabel?: string
  className?: string
}

const defaultIcons = {
  alert: AlertTriangle,
  error: XCircle,
  warning: AlertTriangle
}

export function ErrorState({ 
  title = 'Something went wrong',
  message,
  error,
  icon = 'alert',
  onRetry,
  retryLabel = 'Try Again',
  className 
}: ErrorStateProps) {
  const IconComponent = typeof icon === 'string' ? defaultIcons[icon] : null
  const CustomIcon = typeof icon !== 'string' ? icon : null

  const errorMessage = 
    message || 
    (error instanceof Error ? error.message : typeof error === 'string' ? error : undefined) ||
    'An unexpected error occurred. Please try again.'

  return (
    <div className={clsx(
      'flex flex-col items-center justify-center py-12 px-4 text-center',
      className
    )}>
      <div className="mb-4">
        {IconComponent && (
          <IconComponent className="h-12 w-12 text-red-500" />
        )}
        {CustomIcon && <>{CustomIcon}</>}
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
        {title}
      </h3>
      
      <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md mb-4">
        {errorMessage}
      </p>
      
      {onRetry && (
        <Button
          onClick={onRetry}
          variant="primary"
          size="md"
          leftIcon={<RefreshCw className="h-4 w-4" />}
        >
          {retryLabel}
        </Button>
      )}
    </div>
  )
}




