import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui'
import { Download, RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react'
import { apiHelpers } from '../lib/api'

export default function UpdatesPage() {

  const { data: updates, isLoading, refetch } = useQuery({
    queryKey: ['updates'],
    queryFn: async () => {
      try {
        const response = await apiHelpers.getUpdates?.()
        return Array.isArray(response) ? response : response?.data || []
      } catch (error) {
        console.error('Failed to fetch updates:', error)
        return []
      }
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Updates</h1>
        <p className="mt-2 text-gray-400">
          Manage system updates and check for new versions
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Available Updates</CardTitle>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Check for Updates
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {updates && updates.length > 0 ? (
            <div className="space-y-4">
              {updates.map((update: any) => (
                <div
                  key={update.id}
                  className="flex items-center justify-between p-4 border border-gray-700 rounded-lg bg-gray-800/50"
                >
                  <div className="flex items-center gap-4">
                    {update.status === 'installed' ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : update.status === 'failed' ? (
                      <XCircle className="h-5 w-5 text-red-500" />
                    ) : update.status === 'installing' ? (
                      <Clock className="h-5 w-5 text-yellow-500 animate-spin" />
                    ) : (
                      <Download className="h-5 w-5 text-blue-500" />
                    )}
                    <div>
                      <h3 className="font-semibold text-white">{update.name}</h3>
                      <p className="text-sm text-gray-400">
                        Version {update.version}
                      </p>
                      {update.description && (
                        <p className="text-sm text-gray-500 mt-1">
                          {update.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 text-xs font-medium rounded bg-gray-700 text-gray-300">
                      {update.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-400">No updates available</p>
              <p className="text-sm text-gray-500 mt-2">
                Your system is up to date
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

