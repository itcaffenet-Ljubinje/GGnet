# Frontend Integration Guide

This guide provides information for integrating the new backend features into the frontend.

## New API Endpoints Available

All new endpoints are available through the `apiHelpers` object in `frontend/src/lib/api.ts`.

### Writeback Management

```typescript
// List writebacks
const writebacks = await apiHelpers.getWritebacks({ machine_id: 1 });

// Keep a writeback
await apiHelpers.keepWriteback(writebackId);

// Delete a writeback
await apiHelpers.deleteWriteback(writebackId);
```

### Snapshot Management

```typescript
// List snapshots
const snapshots = await apiHelpers.getSnapshots({ image_id: 1 });

// Create snapshot
const snapshot = await apiHelpers.createSnapshot({
  image_id: 1,
  description: "Backup before update"
});

// Delete snapshot
await apiHelpers.deleteSnapshot(snapshotId);

// Apply retention policy
await apiHelpers.applyRetentionPolicy({
  image_id: 1,
  policy: "KEEP_LAST_N",
  count: 10
});
```

### Scheduler/Job Management

```typescript
// List jobs
const jobs = await apiHelpers.getScheduledJobs();

// Create job
const job = await apiHelpers.createScheduledJob({
  name: "Daily Backup",
  job_type: "backup",
  schedule_type: "cron",
  schedule_data: { cron: "0 2 * * *" },
  behavior_data: { image_ids: [1, 2, 3] }
});

// Pause/Resume job
await apiHelpers.pauseScheduledJob(jobId);
await apiHelpers.resumeScheduledJob(jobId);

// Run job immediately
await apiHelpers.runScheduledJob(jobId);

// Get job executions
const executions = await apiHelpers.getJobExecutions(jobId);
```

### Activity Logging

```typescript
// Get activities
const activities = await apiHelpers.getActivities({
  activity_type: "machine_create",
  level: "info",
  limit: 50
});

// Get activity statistics
const stats = await apiHelpers.getActivityStats({
  start_date: "2025-01-01",
  end_date: "2025-01-31"
});
```

### Batch Operations

```typescript
// Batch image backup
const operation = await apiHelpers.batchBackupImages({
  image_ids: [1, 2, 3],
  backup_path: "/backups/images"
});

// Batch machine operations
const batchOp = await apiHelpers.batchOperateMachines({
  machine_ids: [1, 2, 3],
  operation_type: "machine_restart"
});

// Get operation status
const status = await apiHelpers.getBatchOperation(operationId);

// Cancel operation
await apiHelpers.cancelBatchOperation(operationId);
```

### VM Management

```typescript
// List VMs
const vms = await apiHelpers.getVMs();

// Create VM
const vm = await apiHelpers.createVM({
  name: "Test VM",
  image_id: 1,
  vcpus: 2,
  ram_mb: 4096
});

// Start/Stop VM
await apiHelpers.startVM(vmId);
await apiHelpers.stopVM(vmId);

// Get VNC console URL
const vnc = await apiHelpers.getVMVNC(vmId);
```

### Client Management

```typescript
// List clients
const clients = await apiHelpers.getClients();

// Register client
await apiHelpers.registerClient({
  client_id: "client-001",
  hostname: "PC-01",
  mac_address: "00:11:22:33:44:55"
});

// Send message to client
await apiHelpers.sendClientMessage("client-001", {
  type: "command",
  action: "restart"
});

// Broadcast message
await apiHelpers.broadcastMessage({
  type: "notification",
  message: "System maintenance in 10 minutes"
});
```

### Image Import/Export

```typescript
// Import from file path
const image = await apiHelpers.importImage({
  name: "Windows 11",
  source_path: "/path/to/image.vhdx",
  image_type: "system"
});

// Import via upload
const formData = new FormData();
formData.append('file', file);
formData.append('name', 'Windows 11');
const imported = await apiHelpers.importImageUpload(formData);

// Export image
const exportResult = await apiHelpers.exportImage(imageId, {
  format: "vhdx",
  compress: true
});

// Export for download
const downloadInfo = await apiHelpers.exportImageForDownload(imageId, {
  format: "qcow2"
});
```

### Enhanced ZFS

```typescript
// Get ARC statistics
const arcStats = await apiHelpers.getZfsArcStats();

// Get pool IO statistics
const iostat = await apiHelpers.getZfsPoolIostat("pool0");

// Start pool scrub
await apiHelpers.startZfsPoolScrub("pool0");
```

## WebSocket Integration

### Client WebSocket Connection

```typescript
// Connect to client WebSocket
const ws = new WebSocket(`ws://localhost/api/v1/clients/ws/${clientId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message from server:', data);
};

// Send registration
ws.send(JSON.stringify({
  type: "register",
  hostname: "PC-01",
  ip_address: "192.168.1.100",
  mac_address: "00:11:22:33:44:55"
}));

// Send heartbeat
ws.send(JSON.stringify({
  type: "heartbeat"
}));
```

### Progress Tracking

For batch operations and long-running tasks, use the Progress Tracker:

```typescript
// The backend sends progress updates via WebSocket
// Listen for batch operation progress
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'batch_operation_progress_updated') {
    const progress = data.data;
    console.log(`Progress: ${progress.percentage}%`);
    console.log(`Status: ${progress.status}`);
  }
};
```

## React Query Integration

Example using TanStack Query:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiHelpers } from '@/lib/api';

// Query for activities
function useActivities(filters?: { activity_type?: string; level?: string }) {
  return useQuery({
    queryKey: ['activities', filters],
    queryFn: () => apiHelpers.getActivities(filters),
  });
}

// Mutation for creating snapshot
function useCreateSnapshot() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiHelpers.createSnapshot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

// Query for batch operation status
function useBatchOperation(operationId: number) {
  return useQuery({
    queryKey: ['batch-operation', operationId],
    queryFn: () => apiHelpers.getBatchOperation(operationId),
    refetchInterval: 2000, // Poll every 2 seconds
  });
}
```

## Component Examples

### Activity Log Component

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiHelpers } from '@/lib/api';

function ActivityLog() {
  const { data: activities, isLoading } = useQuery({
    queryKey: ['activities'],
    queryFn: () => apiHelpers.getActivities({ limit: 50 }),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {activities?.map(activity => (
        <div key={activity.id}>
          <span>{activity.message}</span>
          <span>{activity.timestamp}</span>
        </div>
      ))}
    </div>
  );
}
```

### Batch Operation Component

```typescript
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiHelpers } from '@/lib/api';

function BatchOperationManager() {
  const { data: operations } = useQuery({
    queryKey: ['batch-operations'],
    queryFn: () => apiHelpers.listBatchOperations(),
  });

  const backupMutation = useMutation({
    mutationFn: apiHelpers.batchBackupImages,
    onSuccess: (data) => {
      // Start polling for status
      console.log('Operation started:', data.id);
    },
  });

  const handleBackup = () => {
    backupMutation.mutate({
      image_ids: [1, 2, 3],
      backup_path: '/backups',
    });
  };

  return (
    <div>
      <button onClick={handleBackup}>Backup Images</button>
      {operations?.map(op => (
        <div key={op.id}>
          <span>{op.operation_type}</span>
          <span>{op.status}</span>
          <span>{op.completed_items}/{op.total_items}</span>
        </div>
      ))}
    </div>
  );
}
```

## Type Definitions

Add these TypeScript types to your project:

```typescript
// Writeback types
interface Writeback {
  id: number;
  machine_id: number;
  image_id: number;
  path: string;
  size: number;
  created_at: string;
}

// Snapshot types
interface Snapshot {
  id: number;
  image_id: number;
  machine_id?: number;
  snapshot_path: string;
  description?: string;
  timestamp: string;
}

// Scheduled Job types
interface ScheduledJob {
  id: number;
  name: string;
  job_type: string;
  schedule_type: string;
  status: string;
  enabled: boolean;
}

// Batch Operation types
interface BatchOperation {
  id: number;
  operation_type: string;
  status: string;
  total_items: number;
  completed_items: number;
  failed_items: number;
}

// VM types
interface VM {
  id: number;
  name: string;
  vm_id: string;
  status: string;
  vcpus: number;
  ram_mb: number;
  vnc_port?: number;
}

// Client types
interface Client {
  id: number;
  client_id: string;
  hostname?: string;
  ip_address?: string;
  status: string;
  is_connected: boolean;
}
```

## Next Steps

1. Create React components for each feature
2. Add routing for new pages
3. Integrate WebSocket connections
4. Add real-time updates using React Query
5. Create forms for creating/editing resources
6. Add progress indicators for long-running operations

## Testing

Use the API helpers in your tests:

```typescript
import { apiHelpers } from '@/lib/api';

test('creates snapshot', async () => {
  const snapshot = await apiHelpers.createSnapshot({
    image_id: 1,
    description: 'Test snapshot'
  });
  
  expect(snapshot.id).toBeDefined();
});
```




