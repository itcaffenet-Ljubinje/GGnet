// Vitest globals are available via globals: true in vitest.config.ts
import { render, screen, waitFor } from '../../__tests__/setup/test-utils'
import userEvent from '@testing-library/user-event'
import { DataTable, Column, Action } from './DataTable'

interface TestItem extends Record<string, unknown> {
  id: number
  name: string
  status: string
  value: number
}

describe('DataTable', () => {
  const mockData: TestItem[] = [
    { id: 1, name: 'Item 1', status: 'active', value: 100 },
    { id: 2, name: 'Item 2', status: 'inactive', value: 200 },
    { id: 3, name: 'Item 3', status: 'active', value: 150 }
  ]

  const mockColumns: Column<TestItem>[] = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'name', label: 'Name', sortable: true },
    { key: 'status', label: 'Status' },
    { key: 'value', label: 'Value', sortable: true }
  ]

  describe('rendering', () => {
    it('should render table with data', () => {
      render(<DataTable data={mockData} columns={mockColumns} />)
      
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      expect(screen.getByText('Item 2')).toBeInTheDocument()
      expect(screen.getByText('Item 3')).toBeInTheDocument()
    })

    it('should render column headers', () => {
      render(<DataTable data={mockData} columns={mockColumns} />)
      
      expect(screen.getByText('ID')).toBeInTheDocument()
      expect(screen.getByText('Name')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Value')).toBeInTheDocument()
    })

    it('should render empty message when no data', () => {
      render(<DataTable data={[]} columns={mockColumns} />)
      
      expect(screen.getByText('No data available')).toBeInTheDocument()
    })

    it('should render custom empty message', () => {
      render(<DataTable data={[]} columns={mockColumns} emptyMessage="Custom empty message" />)
      
      expect(screen.getByText('Custom empty message')).toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('should show loading state', () => {
      render(<DataTable data={mockData} columns={mockColumns} loading={true} />)
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('should not show data when loading', () => {
      render(<DataTable data={mockData} columns={mockColumns} loading={true} />)
      
      expect(screen.queryByText('Item 1')).not.toBeInTheDocument()
    })
  })

  describe('search functionality', () => {
    it('should show search input when searchable is true', () => {
      render(<DataTable data={mockData} columns={mockColumns} searchable={true} />)
      
      expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument()
    })

    it('should hide search input when searchable is false', () => {
      render(<DataTable data={mockData} columns={mockColumns} searchable={false} />)
      
      expect(screen.queryByPlaceholderText('Search...')).not.toBeInTheDocument()
    })

    it('should filter data based on search term', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} searchable={true} />)
      
      const searchInput = screen.getByPlaceholderText('Search...')
      await user.type(searchInput, 'Item 1')
      
      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument()
        expect(screen.queryByText('Item 2')).not.toBeInTheDocument()
        expect(screen.queryByText('Item 3')).not.toBeInTheDocument()
      })
    })

    it('should search across all columns', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} searchable={true} />)
      
      const searchInput = screen.getByPlaceholderText('Search...')
      await user.clear(searchInput)
      await user.type(searchInput, 'inactive')
      
      await waitFor(() => {
        expect(screen.getByText('Item 2')).toBeInTheDocument()
        expect(screen.queryByText('Item 1')).not.toBeInTheDocument()
        expect(screen.queryByText('Item 3')).not.toBeInTheDocument()
      })
    })
  })

  describe('sorting', () => {
    it('should show sort indicator when column is sorted', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)
      
      const idHeader = screen.getByText('ID').closest('th')
      if (idHeader) {
        await user.click(idHeader)
        
        await waitFor(() => {
          expect(screen.getByText('↑')).toBeInTheDocument()
        })
      }
    })

    it('should toggle sort direction on second click', async () => {
      const user = userEvent.setup()
      render(<DataTable data={mockData} columns={mockColumns} />)
      
      const idHeader = screen.getByText('ID').closest('th')
      if (idHeader) {
        await user.click(idHeader)
        await waitFor(() => {
          expect(screen.getByText('↑')).toBeInTheDocument()
        })
        
        await user.click(idHeader)
        await waitFor(() => {
          expect(screen.getByText('↓')).toBeInTheDocument()
        })
      }
    })

    it('should not allow sorting on non-sortable columns', () => {
      render(<DataTable data={mockData} columns={mockColumns} />)
      
      const statusHeader = screen.getByText('Status').closest('th')
      expect(statusHeader).not.toHaveClass('cursor-pointer')
    })
  })

  describe('custom render', () => {
    it('should use custom render function', () => {
      const columnsWithRender: Column<TestItem>[] = [
        { 
          key: 'status', 
          label: 'Status',
          render: (value) => <span className="badge">{String(value)}</span>
        }
      ]
      
      render(<DataTable data={mockData} columns={columnsWithRender} />)
      
      const badges = screen.getAllByText('active')
      expect(badges.length).toBeGreaterThan(0)
      const badge = badges[0].closest('.badge')
      expect(badge).toBeInTheDocument()
    })
  })

  describe('actions', () => {
    const mockActions: Action<TestItem>[] = [
      {
        label: 'Edit',
        onClick: vi.fn(),
        variant: 'primary'
      },
      {
        label: 'Delete',
        onClick: vi.fn(),
        variant: 'danger'
      }
    ]

    it('should render actions column when actions provided', () => {
      render(<DataTable data={mockData} columns={mockColumns} actions={mockActions} />)
      
      expect(screen.getByText('Actions')).toBeInTheDocument()
    })

    it('should not render actions column when no actions', () => {
      render(<DataTable data={mockData} columns={mockColumns} />)
      
      expect(screen.queryByText('Actions')).not.toBeInTheDocument()
    })

    it('should call action onClick when action button is clicked', async () => {
      const user = userEvent.setup()
      const mockOnClick = vi.fn()
      const actions: Action<TestItem>[] = [
        {
          label: 'Edit',
          onClick: mockOnClick
        }
      ]
      
      render(<DataTable data={mockData} columns={mockColumns} actions={actions} />)
      
      const actionButtons = screen.getAllByTitle('Edit')
      await user.click(actionButtons[0])
      
      expect(mockOnClick).toHaveBeenCalledWith(mockData[0])
    })
  })

  describe('create button', () => {
    it('should show create button when onCreate is provided', () => {
      const mockOnCreate = vi.fn()
      render(<DataTable data={mockData} columns={mockColumns} onCreate={mockOnCreate} />)
      
      expect(screen.getByText('Create New')).toBeInTheDocument()
    })

    it('should use custom create label', () => {
      const mockOnCreate = vi.fn()
      render(
        <DataTable 
          data={mockData} 
          columns={mockColumns} 
          onCreate={mockOnCreate}
          createLabel="Add Item"
        />
      )
      
      expect(screen.getByText('Add Item')).toBeInTheDocument()
    })

    it('should call onCreate when create button is clicked', async () => {
      const user = userEvent.setup()
      const mockOnCreate = vi.fn()
      render(<DataTable data={mockData} columns={mockColumns} onCreate={mockOnCreate} />)
      
      const createButton = screen.getByText('Create New')
      await user.click(createButton)
      
      expect(mockOnCreate).toHaveBeenCalledTimes(1)
    })
  })

  describe('filterable', () => {
    it('should show filter button when filterable is true', () => {
      render(<DataTable data={mockData} columns={mockColumns} filterable={true} />)
      
      expect(screen.getByText('Filter')).toBeInTheDocument()
    })

    it('should hide filter button when filterable is false', () => {
      render(<DataTable data={mockData} columns={mockColumns} filterable={false} />)
      
      expect(screen.queryByText('Filter')).not.toBeInTheDocument()
    })
  })

  describe('column width', () => {
    it('should apply custom column width', () => {
      const columnsWithWidth: Column<TestItem>[] = [
        { key: 'id', label: 'ID', width: '100px' }
      ]
      
      render(<DataTable data={mockData} columns={columnsWithWidth} />)
      
      const header = screen.getByText('ID').closest('th')
      expect(header).toHaveStyle({ width: '100px' })
    })
  })
})

