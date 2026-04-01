/**
 * useQueryState Hook
 * Standardized hook for handling query loading, error, and empty states
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query'
import { ErrorState } from '../components/ui/ErrorState'
import { EmptyState } from '../components/ui/EmptyState'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ReactNode } from 'react'

interface UseQueryStateOptions<T> {
  query: UseQueryResult<T>
  emptyMessage?: string
  emptyDescription?: string
  emptyIcon?: 'inbox' | 'search' | 'folder' | 'database' | ReactNode
  emptyAction?: {
    label: string
    onClick: () => void
  }
  errorTitle?: string
  errorMessage?: string
  loadingText?: string
  showEmptyState?: (data: T) => boolean
}

interface QueryStateRenderProps {
  isLoading: boolean
  error: Error | null
  isEmpty: boolean
  renderContent: () => ReactNode
  renderLoading: () => ReactNode
  renderError: () => ReactNode
  renderEmpty: () => ReactNode
}

/**
 * Hook for standardized query state handling
 */
export function useQueryState<T>({
  query,
  emptyMessage = 'No data available',
  emptyDescription,
  emptyIcon = 'inbox',
  emptyAction,
  errorTitle = 'Something went wrong',
  errorMessage,
  loadingText = 'Loading...',
  showEmptyState = (data: T) => {
    if (Array.isArray(data)) return data.length === 0
    return !data
  }
}: UseQueryStateOptions<T>): QueryStateRenderProps {
  const { data, isLoading, error, refetch } = query

  const isEmpty = !isLoading && !error && data !== undefined && showEmptyState(data)

  const renderLoading = () => (
    <div className="flex items-center justify-center py-12">
      <LoadingSpinner size="lg" text={loadingText} />
    </div>
  )

  const renderError = () => (
    <ErrorState
      title={errorTitle}
      message={errorMessage}
      error={error as Error}
      onRetry={() => refetch()}
    />
  )

  const renderEmpty = () => (
    <EmptyState
      title={emptyMessage}
      description={emptyDescription}
      icon={emptyIcon}
      action={emptyAction}
    />
  )

  const renderContent = () => {
    if (isLoading) return renderLoading()
    if (error) return renderError()
    if (isEmpty) return renderEmpty()
    return null
  }

  return {
    isLoading,
    error: error as Error | null,
    isEmpty,
    renderContent,
    renderLoading,
    renderError,
    renderEmpty
  }
}




