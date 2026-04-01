/**
 * StatusLED Component
 * Visual status indicator with LED-style appearance
 */

import { clsx } from 'clsx'

export type LEDStatus = 'green' | 'amber' | 'red' | 'off'

interface StatusLEDProps {
  status: LEDStatus
  label?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  animated?: boolean
}

export function StatusLED({ 
  status, 
  label, 
  size = 'md',
  className,
  animated = false 
}: StatusLEDProps) {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  }

  const statusClasses = {
    green: 'bg-green-500 shadow-green-500/50',
    amber: 'bg-amber-500 shadow-amber-500/50',
    red: 'bg-red-500 shadow-red-500/50',
    off: 'bg-gray-400 shadow-gray-400/50'
  }

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <div
        className={clsx(
          'rounded-full',
          sizeClasses[size],
          statusClasses[status],
          animated && status !== 'off' && 'animate-pulse',
          'shadow-lg'
        )}
        aria-label={`Status: ${status}`}
      />
      {label && (
        <span className="text-sm text-gray-700 dark:text-gray-300">
          {label}
        </span>
      )}
    </div>
  )
}




