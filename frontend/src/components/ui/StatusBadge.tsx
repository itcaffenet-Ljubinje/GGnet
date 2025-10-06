// React is available globally
import { clsx } from 'clsx'
import { CheckCircle, AlertCircle, XCircle, Info } from 'lucide-react'

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'info' | 'active' | 'inactive' | string
  text: string
  className?: string
  showIcon?: boolean
}

export function StatusBadge({ 
  status, 
  text, 
  className, 
  showIcon = true 
}: StatusBadgeProps) {
  const getStatusConfig = (status: StatusBadgeProps['status']) => {
    switch (status) {
      case 'success':
      case 'active':
        return {
          icon: CheckCircle,
          classes: 'text-green-600 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
          iconClasses: 'text-green-500'
        }
      case 'warning':
        return {
          icon: AlertCircle,
          classes: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
          iconClasses: 'text-yellow-500'
        }
      case 'error':
        return {
          icon: XCircle,
          classes: 'text-red-600 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
          iconClasses: 'text-red-500'
        }
      case 'info':
        return {
          icon: Info,
          classes: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
          iconClasses: 'text-blue-500'
        }
      case 'inactive':
        return {
          icon: XCircle,
          classes: 'text-gray-600 bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800',
          iconClasses: 'text-gray-500'
        }
      default:
        return {
          icon: Info,
          classes: 'text-gray-600 bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800',
          iconClasses: 'text-gray-500'
        }
    }
  }

  const config = getStatusConfig(status)
  const Icon = config.icon

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border',
        config.classes,
        className
      )}
    >
      {showIcon && <Icon className={clsx('h-3 w-3', config.iconClasses)} />}
      {text}
    </span>
  )
}
