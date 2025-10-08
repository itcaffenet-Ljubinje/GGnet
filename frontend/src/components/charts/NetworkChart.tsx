import { lazy, Suspense } from 'react'
import { LoadingSpinner } from '../LoadingSpinner'

// Lazy load the chart content
const LazyChartContent = lazy(() => import('./NetworkChartContent'))

interface NetworkChartProps {
  data: Array<{
    time: string
    value: number
  }>
  dataKey?: string
  color?: string
  height?: number
  label?: string
}

export default function NetworkChart(props: NetworkChartProps) {
  const { height = 300 } = props
  
  return (
    <Suspense fallback={
      <div style={{ height }} className="flex items-center justify-center">
        <LoadingSpinner />
      </div>
    }>
      <LazyChartContent {...props} />
    </Suspense>
  )
}