# WebSocket Integration

The frontend uses WebSocket for real-time communication with the backend, providing live updates for machine status, VM state, and other system events.

## WebSocket Connection

### Connection Setup

**hooks/useWebSocket.js:**
```javascript
import { useEffect, useState, useRef } from 'react'

export function useWebSocket(url) {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState([])
  const reconnectTimeoutRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setSocket(ws)
      setConnected(true)
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      setMessages(prev => [...prev, message])
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setSocket(null)
      setConnected(false)
      
      // Reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        setSocket(new WebSocket(url))
      }, 5000)
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      ws.close()
    }
  }, [url])

  const sendMessage = (message) => {
    if (socket && connected) {
      socket.send(JSON.stringify(message))
    }
  }

  return { socket, connected, messages, sendMessage }
}
```

## WebSocket Context

### WebSocket Provider

**contexts/WebSocketContext.jsx:**
```javascript
import { createContext, useContext } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'

const WebSocketContext = createContext()

export function WebSocketProvider({ children }) {
  const wsUrl = process.env.VITE_WS_URL || 'ws://localhost:8000/hubs/clients'
  const { socket, connected, messages, sendMessage } = useWebSocket(wsUrl)

  return (
    <WebSocketContext.Provider value={{
      socket,
      connected,
      messages,
      sendMessage
    }}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocketContext() {
  return useContext(WebSocketContext)
}
```

## Real-time Updates

### Machine Status Updates

**hooks/useMachineStatus.js:**
```javascript
import { useEffect, useState } from 'react'
import { useWebSocketContext } from '../contexts/WebSocketContext'

export function useMachineStatus(machineId) {
  const { messages, connected } = useWebSocketContext()
  const [status, setStatus] = useState(null)

  useEffect(() => {
    if (!connected) return

    const statusMessages = messages.filter(
      msg => msg.event === 'status' && msg.data.client_id === machineId
    )

    if (statusMessages.length > 0) {
      const latestStatus = statusMessages[statusMessages.length - 1]
      setStatus(latestStatus.data)
    }
  }, [messages, machineId, connected])

  return status
}
```

### VM Status Updates

**hooks/useVMStatus.js:**
```javascript
import { useEffect, useState } from 'react'
import { useWebSocketContext } from '../contexts/WebSocketContext'

export function useVMStatus(vmId) {
  const { messages, connected } = useWebSocketContext()
  const [status, setStatus] = useState(null)

  useEffect(() => {
    if (!connected) return

    const statusMessages = messages.filter(
      msg => msg.event === 'vm_status' && msg.data.vm_id === vmId
    )

    if (statusMessages.length > 0) {
      const latestStatus = statusMessages[statusMessages.length - 1]
      setStatus(latestStatus.data)
    }
  }, [messages, vmId, connected])

  return status
}
```

## Message Types

### Client Messages

**Client Registration:**
```javascript
{
  event: 'register',
  data: {
    client_id: 'client-001',
    mac: '00:11:22:33:44:55',
    ip: '192.168.1.100',
    name: 'PC-1'
  }
}
```

**Status Update:**
```javascript
{
  event: 'status',
  data: {
    client_id: 'client-001',
    status: 'online',
    uptime: '02:30:45',
    speed: '100Mbps',
    sent: '50G',
    received: '5G'
  }
}
```

**Heartbeat:**
```javascript
{
  event: 'heartbeat',
  data: {
    client_id: 'client-001',
    timestamp: '2024-01-01T12:00:00Z'
  }
}
```

### Server Messages

**Command:**
```javascript
{
  event: 'command',
  data: {
    client_id: 'client-001',
    command: 'rename_pc',
    params: {
      new_name: 'PC-1-Updated'
    }
  }
}
```

**VM Status:**
```javascript
{
  event: 'vm_status',
  data: {
    vm_id: 'vm-001',
    status: 'running',
    uptime: '01:30:00',
    vnc_url: 'ws://localhost:6080/vnc.html'
  }
}
```

**Broadcast:**
```javascript
{
  event: 'broadcast',
  data: {
    message: 'System maintenance in 5 minutes'
  }
}
```

## Usage Examples

### Using WebSocket in Components

```javascript
import { useWebSocketContext } from '../contexts/WebSocketContext'
import { useMachineStatus } from '../hooks/useMachineStatus'

function MachineRow({ machine }) {
  const { connected, sendMessage } = useWebSocketContext()
  const status = useMachineStatus(machine.id)

  const handleCommand = (command, params) => {
    sendMessage({
      event: 'command',
      data: {
        client_id: machine.id,
        command,
        params
      }
    })
  }

  return (
    <tr>
      <td>{machine.name}</td>
      <td>{status?.status || 'unknown'}</td>
      <td>{status?.uptime || '-'}</td>
      <td>
        <button onClick={() => handleCommand('reboot', {})}>
          Reboot
        </button>
      </td>
    </tr>
  )
}
```

### Real-time Status Display

```javascript
import { useMachineStatus } from '../hooks/useMachineStatus'

function MachineStatus({ machineId }) {
  const status = useMachineStatus(machineId)

  if (!status) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <div>Status: {status.status}</div>
      <div>Uptime: {status.uptime}</div>
      <div>Speed: {status.speed}</div>
      <div>Sent: {status.sent}</div>
      <div>Received: {status.received}</div>
    </div>
  )
}
```

## SignalR Integration

### SignalR Client Setup

For SignalR compatibility, use SignalR client:

```javascript
import * as signalR from '@microsoft/signalr'

export function useSignalR(url) {
  const [connection, setConnection] = useState(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const conn = new signalR.HubConnectionBuilder()
      .withUrl(url)
      .withAutomaticReconnect()
      .build()

    conn.start()
      .then(() => {
        setConnection(conn)
        setConnected(true)
      })
      .catch(err => console.error('SignalR connection error:', err))

    conn.onclose(() => {
      setConnected(false)
    })

    return () => {
      conn.stop()
    }
  }, [url])

  return { connection, connected }
}
```

## Error Handling

### Error Handling Example

```javascript
import { useWebSocketContext } from '../contexts/WebSocketContext'

function WebSocketStatus() {
  const { connected, socket } = useWebSocketContext()

  if (!connected) {
    return <div>WebSocket disconnected. Reconnecting...</div>
  }

  return <div>WebSocket connected</div>
}
```

## Development Notes

- WebSocket connection is established on app startup
- Automatic reconnection on disconnect
- Messages are filtered by event type and data
- Real-time updates are handled via hooks
- SignalR compatibility is available via SignalR client

## To-Do

- [ ] Add message queuing for offline mode
- [ ] Implement message acknowledgment
- [ ] Add message compression
- [ ] Implement message encryption
- [ ] Add connection status indicators
- [ ] Implement message history

