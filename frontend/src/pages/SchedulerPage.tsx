import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiHelpers } from '../lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Clock, Play, Pause, Trash2, Plus, Edit, CheckCircle, XCircle, AlertCircle, Calendar } from 'lucide-react'
import toast from 'react-hot-toast'

interface ScheduledJob {
  id: number
  name: string
  job_type: string
  schedule_type: string
  schedule_data: Record<string, unknown>
  behavior_data: Record<string, unknown>
  status: string
  enabled: boolean
  created_at: string
  updated_at: string
}

interface JobExecution {
  id: number
  job_id: number
  status: string
  started_at: string
  completed_at?: string
  output?: string
  error?: string
}

export default function SchedulerPage() {
  const [selectedJob, setSelectedJob] = useState<number | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['scheduled-jobs'],
    queryFn: () => apiHelpers.getScheduledJobs(),
  })

  const { data: executions } = useQuery({
    queryKey: ['job-executions', selectedJob],
    queryFn: () => selectedJob ? apiHelpers.getJobExecutions(selectedJob) : null,
    enabled: !!selectedJob,
  })

  const { data: behaviors } = useQuery({
    queryKey: ['behaviors'],
    queryFn: () => apiHelpers.getBehaviors(),
  })

  const pauseMutation = useMutation({
    mutationFn: apiHelpers.pauseScheduledJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] })
      toast.success('Job paused successfully')
    },
    onError: () => {
      toast.error('Failed to pause job')
    },
  })

  const resumeMutation = useMutation({
    mutationFn: apiHelpers.resumeScheduledJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] })
      toast.success('Job resumed successfully')
    },
    onError: () => {
      toast.error('Failed to resume job')
    },
  })

  const runNowMutation = useMutation({
    mutationFn: apiHelpers.runScheduledJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-executions'] })
      toast.success('Job started successfully')
    },
    onError: () => {
      toast.error('Failed to run job')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: apiHelpers.deleteScheduledJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] })
      toast.success('Job deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete job')
    },
  })

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'running':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />
      case 'failed':
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'running':
        return 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
      case 'paused':
        return 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300'
      case 'failed':
      case 'error':
        return 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
      default:
        return 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
    }
  }

  const formatSchedule = (job: ScheduledJob) => {
    if (job.schedule_type === 'cron' && job.schedule_data.cron) {
      return `Cron: ${job.schedule_data.cron}`
    }
    if (job.schedule_type === 'interval' && job.schedule_data.seconds) {
      return `Every ${job.schedule_data.seconds} seconds`
    }
    if (job.schedule_type === 'once' && job.schedule_data.run_date) {
      return `Once: ${new Date(job.schedule_data.run_date as string).toLocaleString()}`
    }
    return job.schedule_type
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const handlePause = (id: number) => {
    pauseMutation.mutate(id)
  }

  const handleResume = (id: number) => {
    resumeMutation.mutate(id)
  }

  const handleRunNow = (id: number) => {
    runNowMutation.mutate(id)
  }

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this scheduled job?')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Scheduler</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage scheduled jobs and automation</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Create Job
        </button>
      </div>

      {/* Statistics */}
      {jobs && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Jobs</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{jobs.length || 0}</p>
                </div>
                <Clock className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Active</p>
                  <p className="text-2xl font-bold text-green-600">
                    {jobs.filter((j: ScheduledJob) => j.status === 'active').length}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Paused</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {jobs.filter((j: ScheduledJob) => j.status === 'paused').length}
                  </p>
                </div>
                <Pause className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Failed</p>
                  <p className="text-2xl font-bold text-red-600">
                    {jobs.filter((j: ScheduledJob) => j.status === 'failed').length}
                  </p>
                </div>
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Jobs List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Scheduled Jobs</CardTitle>
              <CardDescription>Automated tasks and scheduled operations</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : jobs && jobs.length > 0 ? (
                <div className="space-y-3">
                  {jobs.map((job: ScheduledJob) => (
                    <div
                      key={job.id}
                      className={`p-4 border rounded-lg transition-all hover:shadow-md ${
                        selectedJob === job.id
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700'
                      }`}
                      onClick={() => setSelectedJob(job.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Clock className="h-5 w-5 text-blue-500" />
                            <h3 className="font-semibold text-gray-900 dark:text-white">{job.name}</h3>
                            <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(job.status)}`}>
                              {job.status}
                            </span>
                            {getStatusIcon(job.status)}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                            <p><span className="font-medium">Type:</span> {job.job_type}</p>
                            <p><span className="font-medium">Schedule:</span> {formatSchedule(job)}</p>
                            <p className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              Created: {formatTimestamp(job.created_at)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1 ml-4">
                          {job.status === 'active' ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handlePause(job.id)
                              }}
                              disabled={pauseMutation.isPending}
                              className="p-2 text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded-lg transition-colors"
                              title="Pause job"
                            >
                              <Pause className="h-4 w-4" />
                            </button>
                          ) : (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleResume(job.id)
                              }}
                              disabled={resumeMutation.isPending}
                              className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                              title="Resume job"
                            >
                              <Play className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleRunNow(job.id)
                            }}
                            disabled={runNowMutation.isPending}
                            className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                            title="Run now"
                          >
                            <Play className="h-4 w-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDelete(job.id)
                            }}
                            disabled={deleteMutation.isPending}
                            className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            title="Delete job"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Clock className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No scheduled jobs found</p>
                  <p className="text-sm mt-2">Create a new job to get started</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Execution History */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Execution History</CardTitle>
              <CardDescription>
                {selectedJob ? 'Recent executions for selected job' : 'Select a job to view history'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedJob ? (
                executions && executions.length > 0 ? (
                  <div className="space-y-3">
                    {executions.slice(0, 10).map((execution: JobExecution) => (
                      <div
                        key={execution.id}
                        className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          {getStatusIcon(execution.status)}
                          <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(execution.status)}`}>
                            {execution.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          Started: {formatTimestamp(execution.started_at)}
                        </p>
                        {execution.completed_at && (
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Completed: {formatTimestamp(execution.completed_at)}
                          </p>
                        )}
                        {execution.error && (
                          <p className="text-xs text-red-600 dark:text-red-400 mt-1 truncate">
                            {execution.error}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <p>No executions found</p>
                  </div>
                )
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <p>Select a job to view execution history</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Create Job Modal - Placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Create Scheduled Job</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Job creation form will be implemented here. This requires integration with the behavior system.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}




