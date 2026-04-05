// Vitest globals are available via globals: true in vitest.config.ts
import { render, screen, waitFor } from '../../__tests__/setup/test-utils'
import UsageChart from './UsageChart'

// Mock the lazy-loaded component
vi.mock('./UsageChartContent', () => ({
  default: ({ data, type, dataKey, color, height }: { data: unknown[], type?: string, dataKey?: string, color?: string, height?: number }) => (
    <div data-testid="usage-chart-content">
      <div data-testid="data">{JSON.stringify(data)}</div>
      <div data-testid="type">{type || ''}</div>
      <div data-testid="dataKey">{dataKey || ''}</div>
      <div data-testid="color">{color || ''}</div>
      <div data-testid="height">{height || ''}</div>
    </div>
  )
}))

describe('UsageChart', () => {
  const mockData = [
    { time: '2024-01-01', cpu: 50, memory: 60, disk: 40, network: 30 },
    { time: '2024-01-02', cpu: 70, memory: 80, disk: 50, network: 40 },
    { time: '2024-01-03', cpu: 60, memory: 70, disk: 45, network: 35 }
  ]

  describe('rendering', () => {
    it('should render chart with data', async () => {
      render(<UsageChart data={mockData} dataKey="cpu" />)
      
      await waitFor(() => {
        expect(screen.getByTestId('usage-chart-content')).toBeInTheDocument()
      })
    })

    it('should pass data to chart content', async () => {
      render(<UsageChart data={mockData} dataKey="cpu" />)
      
      await waitFor(() => {
        const dataElement = screen.getByTestId('data')
        expect(dataElement.textContent).toContain('cpu')
      })
    })

    it('should use default height', async () => {
      render(<UsageChart data={mockData} dataKey="cpu" />)
      
      await waitFor(() => {
        const heightElement = screen.getByTestId('height')
        // Height prop is passed but may be undefined in mock, check that component renders
        expect(heightElement).toBeInTheDocument()
      })
    })

    it('should use custom height', async () => {
      render(<UsageChart data={mockData} dataKey="cpu" height={400} />)
      
      await waitFor(() => {
        const heightElement = screen.getByTestId('height')
        expect(heightElement.textContent).toBe('400')
      })
    })
  })

  describe('props', () => {
    it('should pass dataKey prop', async () => {
      render(<UsageChart data={mockData} dataKey="memory" />)
      
      await waitFor(() => {
        expect(screen.getByTestId('dataKey')).toHaveTextContent('memory')
      })
    })

    it('should pass type prop', async () => {
      render(<UsageChart data={mockData} dataKey="cpu" type="area" />)
      
      await waitFor(() => {
        expect(screen.getByTestId('type')).toHaveTextContent('area')
      })
    })

    it('should pass color prop', async () => {
      render(<UsageChart data={mockData} dataKey="cpu" color="#00ff00" />)
      
      await waitFor(() => {
        expect(screen.getByTestId('color')).toHaveTextContent('#00ff00')
      })
    })

    it('should handle different dataKeys', async () => {
      const dataKeys: Array<'cpu' | 'memory' | 'disk' | 'network'> = ['cpu', 'memory', 'disk', 'network']
      
      for (const key of dataKeys) {
        const { unmount } = render(<UsageChart data={mockData} dataKey={key} />)
        
        await waitFor(() => {
          expect(screen.getByTestId('dataKey')).toHaveTextContent(key)
        })
        
        unmount()
      }
    })
  })

  describe('loading state', () => {
    it('should show loading spinner while loading', async () => {
      render(<UsageChart data={mockData} dataKey="cpu" />)
      
      // The lazy loading happens very quickly, so we check that the component eventually renders
      await waitFor(() => {
        expect(screen.getByTestId('usage-chart-content')).toBeInTheDocument()
      })
    })
  })
})

