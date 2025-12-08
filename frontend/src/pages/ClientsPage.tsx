import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiHelpers } from '../lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Monitor, Wifi, WifiOff, Send, MessageSquare, CheckCircle, Clock, Server } from 'lucide-react'
import toast from 'react-hot-toast'

interface Client {
  id: number
  client_id: string
  machine_id?: number
  hostname?: string
  ip_address?: string
  os_version?: string
  status: string
  last_seen?: string
  is_connected: boolean
  machine?: {
    name: string
  }
}

export default function ClientsPage() {
  const [selectedClient, setSelectedClient] = useState<string | null>(null)
  const [messageText, setMessageText] = useState('')

  const { data: clients, isLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: () => apiHelpers.getClients(),
  })

  const { data: connectedClients } = useQuery({
    queryKey: ['connected-clients'],
    queryFn: () => apiHelpers.getConnectedClients(),
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const { data: clientDetails } = useQuery({
    queryKey: ['client', selectedClient],
    queryFn: () => selectedClient ? apiHelpers.getClient(selectedClient) : null,
    enabled: !!selectedClient,
  })

  const { data: clientStatus } = useQuery({
    queryKey: ['client-status', selectedClient],
    queryFn: () => selectedClient ? apiHelpers.getClientStatus(selectedClient) : null,
    enabled: !!selectedClient,
    refetchInterval: 3000, // Refresh every 3 seconds for status
  })

  const sendMessageMutation = useMutation({
    mutationFn: ({ clientId, message }: { clientId: string; message: Record<string, unknown> }) =>
      apiHelpers.sendClientMessage(clientId, message),
    onSuccess: () => {
      toast.success('Message sent successfully')
      setMessageText('')
    },
    onError: () => {
      toast.error('Failed to send message')
    },
  })

  const broadcastMutation = useMutation({
    mutationFn: (message: Record<string, unknown>) => apiHelpers.broadcastMessage(message),
    onSuccess: () => {
      toast.success('Message broadcasted successfully')
      setMessageText('')
    },
    onError: () => {
      toast.error('Failed to broadcast message')
    },
  })

  const getStatusIcon = (isConnected: boolean) => {
    return isConnected ? (
      <CheckCircle className="h-4 w-4 text-green-500" />
    ) : (
      <WifiOff className="h-4 w-4 text-gray-500" />
    )
  }

  const getStatusColor = (isConnected: boolean) => {
    return isConnected
      ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
      : 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
  }

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Never'
    return new Date(timestamp).toLocaleString()
  }

  const handleSendMessage = () => {
    if (!selectedClient || !messageText.trim()) {
      toast.error('Please select a client and enter a message')
      return
    }
    sendMessageMutation.mutate({
      clientId: selectedClient,
      message: { type: 'message', content: messageText },
    })
  }

  const handleBroadcast = () => {
    if (!messageText.trim()) {
      toast.error('Please enter a message')
      return
    }
    if (confirm('Send this message to all connected clients?')) {
      broadcastMutation.mutate({ type: 'broadcast', content: messageText })
    }
  }

  const connectedClientIds = connectedClients || []
  const isClientConnected = (clientId: string) => connectedClientIds.includes(clientId)

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Clients</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage Windows client connections</p>
        </div>
      </div>

      {/* Statistics */}
      {clients && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Clients</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{clients.length || 0}</p>
                </div>
                <Monitor className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Connected</p>
                  <p className="text-2xl font-bold text-green-600">
                    {clients.filter((c: Client) => isClientConnected(c.client_id)).length}
                  </p>
                </div>
                <Wifi className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Offline</p>
                  <p className="text-2xl font-bold text-gray-600">
                    {clients.filter((c: Client) => !isClientConnected(c.client_id)).length}
                  </p>
                </div>
                <WifiOff className="h-8 w-8 text-gray-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Connections</p>
                  <p className="text-2xl font-bold text-blue-600">{connectedClientIds.length}</p>
                </div>
                <Server className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clients List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Client Machines</CardTitle>
              <CardDescription>Windows client connections and status</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : clients && clients.length > 0 ? (
                <div className="space-y-3">
                  {clients.map((client: Client) => {
                    const connected = isClientConnected(client.client_id)
                    return (
                      <div
                        key={client.id}
                        className={`p-4 border rounded-lg transition-all hover:shadow-md ${
                          selectedClient === client.client_id
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700'
                        }`}
                        onClick={() => setSelectedClient(client.client_id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Monitor className="h-5 w-5 text-blue-500" />
                              <h3 className="font-semibold text-gray-900 dark:text-white">
                                {client.hostname || client.client_id}
                              </h3>
                              <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(connected)}`}>
                                {connected ? 'Connected' : 'Offline'}
                              </span>
                              {getStatusIcon(connected)}
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                              <p><span className="font-medium">Client ID:</span> {client.client_id}</p>
                              {client.ip_address && (
                                <p><span className="font-medium">IP:</span> {client.ip_address}</p>
                              )}
                              {client.os_version && (
                                <p><span className="font-medium">OS:</span> {client.os_version}</p>
                              )}
                              {client.machine && (
                                <p><span className="font-medium">Machine:</span> {client.machine.name}</p>
                              )}
                              <p className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                Last seen: {formatTimestamp(client.last_seen)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Monitor className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No clients found</p>
                  <p className="text-sm mt-2">Clients will appear here when they connect</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Client Details & Messaging */}
        <div className="lg:col-span-1 space-y-6">
          {/* Client Details */}
          <Card>
            <CardHeader>
              <CardTitle>Client Details</CardTitle>
              <CardDescription>
                {selectedClient ? 'Details for selected client' : 'Select a client to view details'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedClient && clientDetails ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2">General</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500 dark:text-gray-400">Client ID:</span>
                        <span className="text-gray-900 dark:text-white font-mono text-xs">{clientDetails.client_id}</span>
                      </div>
                      {clientDetails.hostname && (
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Hostname:</span>
                          <span className="text-gray-900 dark:text-white">{clientDetails.hostname}</span>
                        </div>
                      )}
                      {clientDetails.ip_address && (
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">IP Address:</span>
                          <span className="text-gray-900 dark:text-white">{clientDetails.ip_address}</span>
                        </div>
                      )}
                      {clientDetails.os_version && (
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">OS Version:</span>
                          <span className="text-gray-900 dark:text-white">{clientDetails.os_version}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  {clientStatus && (
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Connection Status</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Status:</span>
                          <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(clientStatus.is_connected)}`}>
                            {clientStatus.is_connected ? 'Connected' : 'Offline'}
                          </span>
                        </div>
                        {clientStatus.last_seen && (
                          <div className="flex justify-between">
                            <span className="text-gray-500 dark:text-gray-400">Last Seen:</span>
                            <span className="text-gray-900 dark:text-white text-xs">
                              {formatTimestamp(clientStatus.last_seen)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <p>Select a client to view details</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Messaging */}
          <Card>
            <CardHeader>
              <CardTitle>Send Message</CardTitle>
              <CardDescription>Send message to client or broadcast to all</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <textarea
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  placeholder="Enter message..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 resize-none"
                  rows={4}
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSendMessage}
                    disabled={!selectedClient || !messageText.trim() || sendMessageMutation.isPending}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Send className="h-4 w-4" />
                    Send to Client
                  </button>
                  <button
                    onClick={handleBroadcast}
                    disabled={!messageText.trim() || broadcastMutation.isPending}
                    className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <MessageSquare className="h-4 w-4" />
                    Broadcast
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}




