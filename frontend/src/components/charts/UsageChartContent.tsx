import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  AreaChart, 
  Area 
} from 'recharts'

interface UsageChartContentProps {
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

export default function UsageChartContent({ 
  data, 
  type = 'line', 
  dataKey, 
  color = '#3b82f6', 
  height = 300 
}: UsageChartContentProps) {
  const ChartComponent = type === 'area' ? AreaChart : LineChart
  const DataComponent = type === 'area' ? Area : Line

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ChartComponent data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis 
          dataKey="time" 
          stroke="#9ca3af"
          tick={{ fill: '#9ca3af' }}
        />
        <YAxis 
          stroke="#9ca3af"
          tick={{ fill: '#9ca3af' }}
        />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: '#1f2937', 
            border: '1px solid #374151',
            borderRadius: '0.375rem'
          }}
          labelStyle={{ color: '#e5e7eb' }}
        />
        <DataComponent 
          type="monotone" 
          dataKey={dataKey} 
          stroke={color}
          fill={color}
          strokeWidth={2}
          {...(type === 'area' ? { fillOpacity: 0.3 } : {})}
        />
      </ChartComponent>
    </ResponsiveContainer>
  )
}