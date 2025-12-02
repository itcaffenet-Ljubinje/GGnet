import { lazy, Suspense } from 'react'
import type { 
  LineChart as LineChartType, 
  AreaChart as AreaChartType 
} from 'recharts'
import { LoadingSpinner } from '../LoadingSpinner'

// Lazy load the entire chart component
const LazyChartContent = lazy(() => import('./UsageChartContent'))

interface UsageChartProps {
  data: Array<{
    time: string
    cpu: number
    memory: number
    disk: number
    network: number
  }>
  type?: 'line' | 'area'
  dataKey: 'cpu' | 'memory' | 'disk' | 'network'
  color?: string
  height?: number
}

export default function UsageChart(props: UsageChartProps) {
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