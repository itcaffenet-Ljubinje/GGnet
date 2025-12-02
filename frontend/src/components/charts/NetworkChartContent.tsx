import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts'

interface NetworkChartContentProps {
  data: Array<{
    time: string
    value: number
  }>
  dataKey?: string
  color?: string
  height?: number
  label?: string
}

export default function NetworkChartContent({ 
  data, 
  dataKey = 'value', 
  color = '#3b82f6', 
  height = 300,
  label = 'Value'
}: NetworkChartContentProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
          formatter={(value: any) => [`${value}`, label]}
        />
        <Line 
          type="monotone" 
          dataKey={dataKey} 
          stroke={color}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}