# GgRock.Api - Detailed Component Analysis

## 📋 Table of Contents

1. [SignalR Events Detailed Analysis](#1-signalr-events-detailed-analysis)
2. [Service Layer Analysis](#2-service-layer-analysis)
3. [Error Handling Patterns](#3-error-handling-patterns)
4. [Activity Log Actions](#4-activity-log-actions)
5. [Hosted Services & Background Tasks](#5-hosted-services--background-tasks)
6. [Configuration & Environment Variables](#6-configuration--environment-variables)
7. [DTOs and Serialization](#7-dtos-and-serialization)

---

## 1. SignalR Events Detailed Analysis

### 1.1 SignalR Event Constants

**Location**: `QYGfYP56yaQDai3Flj6/jZUwCe5HV0QZ1QhTswf.cs`

All SignalR event names are defined as constants in this static class:

| Constant | Event Name | Purpose |
|----------|------------|---------|
| `BGQo82MopG` | `machine_updated` | Machine state or properties changed |
| `diooXWrB7s` | `machine_client_connection_updated` | Machine client connection status changed |
| `hTyohEdrFV` | `image_updated` | Image properties or status changed |
| `RHroVTFESO` | `image_import_updated` | Image import status changed |
| `cXIorqEeDa` | `image_import_progress_updated` | Image import progress update |
| `dNQoUHplD7` | `image_backup_restore_progress_updated` | Backup/restore progress update |
| `M40oPbNMAU` | `image_backup_restore_updated` | Backup/restore status changed |
| `KiPoDEJnsP` | `machines_connection_state_updated` | Multiple machines connection state changed |
| `XEAoRJv8WN` | `subscription_updated` | Subscription status changed |
| `WkMocXZKD1` | `writeback_info_updated` | Writeback information changed |
| `AYIoBScNDv` | `writeback_states_updated` | Writeback states changed |
| `NTboxCZiW6` | `server_ram_updated` | Server RAM usage updated |
| `pSZowuFIK3` | `version_info_updated` | Version information updated |
| `z0jozZ4VQe` | `vm_info_updated` | VM information updated |
| `LaOHCY1OlY` | `array_updated` | Storage array status changed |
| `urxHGrgGJd` | `array_rebuild_progress_updated` | Array rebuild progress update |
| `JwWHS9V6Ai` | `array_trim_progress_updated` | Array trim progress update |
| `W3EHoDJV1t` | `array_space_threshold_reached` | Array space threshold reached |
| `cqQHHChJ7T` | `machine_boot_failed` | Machine boot failure notification |
| `kV0Hgfhsjj` | `toolchain_download_progress_updated` | Toolchain download progress |
| `RLXHaK4pwI` | `toolchain_state_updated` | Toolchain state changed |
| `viWHEDIO0p` | `toolchain_version_updated` | Toolchain version changed |
| `ysoH615N4E` | `image_download_progress_updated` | Image download progress |
| `ev9H44TIwJ` | `scheduled_machine_actions` | Scheduled machine actions updated |
| `WMQH926DcZ` | `scheduled_machine_boot_states` | Scheduled boot states updated |
| `xgiHv2Ewpj` | `managed_machine_action_executions` | Managed action executions updated |
| `TUoHyb5ygT` | `next_managed_machine_action_executions` | Next action executions updated |
| `w9WH0VBCZ8` | `features_updated` | Feature toggles updated |
| `WyTHOIIvwk` | `activity_log_created` | New activity log entry created |
| `OM2HWsFD90` | `shell_command_execution_progress` | Shell command execution progress |

### 1.2 SignalR Broadcasting Patterns

#### Pattern 1: Broadcast to All Admin Clients
```csharp
_hubContext.Clients.All.SendAsync("event_name", data)
```

**Used For:**
- Machine updates
- Image updates
- Array updates
- Subscription updates
- Feature toggles
- Activity logs

**Location Examples:**
- `bp6rJ0VmT0GhBvTOxRJ/j2SNtvV48GCChTJF4pV.cs` (ImagesController)
- `DpmOQaVDRECQASby228/rt6J6EVix5OjgiriprJ.cs` (BatchImageOperationsController)
- `I9oGCq3pEefcXE6r5tC/pbZpkd35MxKmcFJCV6c.cs` (ImagesController)

#### Pattern 2: Broadcast to Specific Machine
```csharp
_hubContext.Clients.Group(machineId.ToString()).SendAsync("event_name", data)
```

**Used For:**
- Machine-specific updates
- Machine connection state

#### Pattern 3: Broadcast Progress Updates
```csharp
_hubContext.Clients.All.SendAsync("progress_event", progressData)
```

**Used For:**
- Image import progress
- Backup/restore progress
- Array rebuild/trim progress
- Toolchain download progress
- Shell command execution progress

### 1.3 SignalR Hub Context Usage

**Admin Hub Context** (`IHubContext<zUBcN054iJ72Sa5X8Te>`):
- Injected into controllers and services
- Used for broadcasting to Admin clients
- All admin notifications go through this hub

**Machine Hub Context** (`IHubContext<LDXTkw57vvp3uCos5CW>`):
- Injected into controllers and services
- Used for machine-specific communications
- Machines connect to this hub with Machine role

---

## 2. Service Layer Analysis

### 2.1 Service Interfaces

#### Machine Service Interface
**Location**: `SdtQULGSuKPlrYdnEtV/kHoac9GQrbAIsZLprb4.cs`

**Key Methods:**
- `S6xGtTXlVZk()` - Initialize/Refresh machines
- `HkfGtqIvLFC(bool includeDeleted = false)` - Get all machines
- `tGvGt1wgTfb(IReadOnlyCollection<Guid> machineIds)` - Get machines by IDs
- `SYaGtnGn5mE(Guid machineId)` - Get machine by ID
- `L7NGtd7pWhL(Guid machineId)` - Get machine entity by ID
- `zvMGt4PlwaC(string macAddress, bool includeDeleted = false)` - Get machine by MAC
- `mMvGtWEQn6D(Guid machineId, MachineState state, bool force = false)` - Update machine state
- `xIFGtFYWxPm(Guid machineId)` - Create machine
- `yvcGtLIAT3N(Guid machineId, string name)` - Rename machine
- `uqJGtUPyxj2(Guid machineId, Guid imageId, string snapshotName)` - Update machine image
- `a29G2GNbgNm(IReadOnlyCollection<Guid> machineIds)` - Delete machines
- `KwdGt5lDPOa(Guid machineId)` - Delete machine
- `BbSGtICw2At(Guid machineId, bool enabled)` - Enable/disable machine boot
- `JV4Gtmdn1nR(Guid machineId, bool enabled)` - Enable/disable keep writebacks
- `IOfGtz5nlXF(Guid machineId, bool enabled)` - Show/hide machine
- `yysG2Cosnm4(Guid machineId, bool enabled)` - Show/hide writebacks
- `h0RG2S4Hx2M(Guid machineId, Guid imageId, LocalDateTime snapshotDate)` - Schedule snapshot

#### Image Service Interface
**Location**: `b4sxPlGnx7S4G88uVsv/p70Ik4G72411I3PiUUM.cs`

**Key Methods:**
- `r2dG2qwZYvw()` - Get all images
- `VYaG21MFmqe(string imageName, string snapshotName)` - Get image snapshot
- `MQYG2nFN5Wf(string imageName, string snapshotName)` - Get image snapshot info
- `u5AG2dmMmfv(string imageName, string snapshotName, int page = 1)` - Get image snapshots (paginated)
- `VVnG24UP01t(image)` - Get image size
- `v2nG27RnHv5(string imageName)` - Delete image
- `gZ3G2kj8rn7(string imageName)` - Get image path
- `WsZG2yIseg3(string imageName)` - Get image default snapshot
- `tING2W8xXqb(string imageName, string snapshotName, bool lock = false, bool unlock = false)` - Lock/unlock snapshot
- `LNSG2XHw7f2(string imageName, string snapshotName)` - Delete snapshot
- `p5MG2Quy8Tg(string imageName, bool backup = false, bool restore = false)` - Backup/restore image
- `WGBG2Fo18MU(string imageName, string newName)` - Rename image
- `pO7G2LAIKb3(string imageName)` - Get image info
- `LA1G2UFDAZg(string imageName, string snapshotName, string newSnapshotName)` - Rename snapshot
- `e5hG25uiYgc(string imageName)` - Increase image volume

### 2.2 Service Implementation Patterns

#### Pattern 1: Service with Database Context
```csharp
public class Service : IService
{
    private readonly GgRockContext _context;
    private readonly IHubContext<AdminHub> _hubContext;
    private readonly ILogger _logger;
    
    public Service(GgRockContext context, IHubContext<AdminHub> hubContext, ILogger logger)
    {
        _context = context;
        _hubContext = hubContext;
        _logger = logger;
    }
}
```

#### Pattern 2: Service with SignalR Broadcasting
```csharp
public async Task UpdateEntity(Guid id, EntityDto dto)
{
    // Update entity in database
    await _context.SaveChangesAsync();
    
    // Broadcast update via SignalR
    await _hubContext.Clients.All.SendAsync("entity_updated", entity);
}
```

#### Pattern 3: Service with Progress Tracking
```csharp
public async Task LongRunningOperation(Guid id, IProgress<double> progress)
{
    for (int i = 0; i < 100; i++)
    {
        // Do work
        progress.Report(i);
        
        // Broadcast progress via SignalR
        await _hubContext.Clients.All.SendAsync("operation_progress", new { Id = id, Progress = i });
    }
}
```

---

## 3. Error Handling Patterns

### 3.1 Exception Types

#### Custom Exceptions
- `H04vxgxePxI1GFriGmj` - Custom exception for shell command execution
- `OperationCanceledException` - For cancelled operations
- Standard .NET exceptions (`ArgumentException`, `InvalidOperationException`, etc.)

### 3.2 Error Handling in Shell Command Executor

**Location**: `npkiHZSTUj88uldQraA/xH4KpXStfS1nLOYJEXn.cs`

**Pattern:**
```csharp
try
{
    // Execute command
}
catch (Exception ex)
{
    // Lock for thread safety
    lock (_lock)
    {
        // Update command status
        command.Status = CommandStatus.Failed;
        command.FinishedAt = DateTime.UtcNow;
        command.ErrorMessage = ex.Message;
        
        // Log based on exception type
        if (ex is OperationCanceledException && timeout)
        {
            _logger.Warning("Command timeout: {Command}", command.Command);
        }
        else if (ex is OperationCanceledException)
        {
            _logger.Information("Command cancelled: {Command}", command.Command);
        }
        else if (ex is CustomException customEx)
        {
            _logger.Warning(ex, "Command failed: {Error}, {Command}", customEx.Message, command.Command);
        }
        else
        {
            _logger.Error(ex, "Command error: {Command}", command.Command);
        }
        
        // Broadcast error via SignalR if connection ID available
        if (signalRConnectionId != null)
        {
            BroadcastError(signalRConnectionId);
        }
    }
}
```

### 3.3 Error Handling in Controllers

**Pattern:**
```csharp
[HttpPost]
public async Task<IActionResult> Create(CreateDto dto)
{
    try
    {
        // Validate input
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }
        
        // Execute operation
        var result = await _service.CreateAsync(dto);
        
        return Ok(result);
    }
    catch (ArgumentException ex)
    {
        _logger.Warning(ex, "Invalid argument: {Message}", ex.Message);
        return BadRequest(ex.Message);
    }
    catch (InvalidOperationException ex)
    {
        _logger.Warning(ex, "Invalid operation: {Message}", ex.Message);
        return Conflict(ex.Message);
    }
    catch (Exception ex)
    {
        _logger.Error(ex, "Unexpected error creating entity");
        return StatusCode(500, "Internal server error");
    }
}
```

### 3.4 Global Exception Handling

**Not Visible in Decompiled Code:**
- Global exception handler middleware may be present but obfuscated
- ASP.NET Core default exception handling is used
- Serilog exception destructuring for logging

**Recommendations:**
- Implement global exception handler middleware
- Return consistent error response format
- Log all exceptions with context
- Don't expose internal error details to clients

---

## 4. Activity Log Actions

### 4.1 Complete Activity Log Action Enum

**Location**: `GgRock.Domain.SerializableTypes.ActivityLogs/ActivityLogAction.cs`

**Total Actions**: 119

#### Authentication & User Actions (2)
- `Login` - User login
- `ChangePassword` - Password change

#### Server Configuration Actions (15)
- `ChangeServerOwner` - Change server owner
- `EnableGgRockBoot` - Enable GgRock boot
- `DisableGgRockBoot` - Disable GgRock boot
- `ChangeRamSettings` - Change RAM settings
- `ChangeReleaseStream` - Change release stream
- `ChangeSslCertificateDomains` - Change SSL certificate domains
- `EnableAutoImportPoolOnServerStart` - Enable auto import pool
- `DisableAutoImportPoolOnServerStart` - Disable auto import pool
- `ChangeArraySpaceWarningThreshold` - Change array space warning threshold
- `ChangeArraySpaceReservedThreshold` - Change array space reserved threshold
- `ChangeTimeToKeepUnusedSnapshots` - Change snapshot retention time
- `ChangeNumberOfUnprotectedSnapshotsToPreserve` - Change unprotected snapshots count
- `ChangeTimeToKeepUnusedWritebacks` - Change writeback retention time
- `ChangeTrimSettings` - Change trim settings
- `ChangeWakeOnLanSettings` - Change Wake-on-LAN settings
- `EnableMultipleNetworksSupport` - Enable multiple networks
- `DisableMultipleNetworksSupport` - Disable multiple networks
- `EnableSecureBootKeysAutoEnrollment` - Enable Secure Boot auto enrollment
- `DisableSecureBootKeysAutoEnrollment` - Disable Secure Boot auto enrollment
- `ChangeUserIdleTimeout` - Change user idle timeout

#### Server Operations (3)
- `StartGgRockUpdate` - Start GgRock update
- `RestartService` - Restart service
- `RebootServer` - Reboot server

#### Shell Command Actions (2)
- `RunShellCommand` - Execute shell command
- `CancelShellCommandExecution` - Cancel shell command

#### Machine Management Actions (20)
- `CreateMachine` - Create new machine
- `RenameMachine` - Rename machine
- `ChangeMachineMac` - Change machine MAC address
- `ChangeMachineSystemImage` - Change machine system image
- `ChangeMachineSystemImageSnapshot` - Change machine system image snapshot
- `ChangeMachineApplicationImages` - Change machine application images
- `ChangeMachineApplicationImageSnapshot` - Change machine application image snapshot
- `ChangeMachineDisplaySettings` - Change machine display settings
- `HideMachine` - Hide machine
- `ShowMachine` - Show machine
- `EnableMachineGgRockBoot` - Enable machine GgRock boot
- `DisableMachineGgRockBoot` - Disable machine GgRock boot
- `EnableMachineKeepWritebacks` - Enable keep writebacks
- `DisableMachineKeepWritebacks` - Disable keep writebacks
- `HideMachineWritebacks` - Hide machine writebacks
- `ShowMachineWritebacks` - Show machine writebacks
- `DeleteMachine` - Delete machine
- `RestartMachine` - Restart machine
- `ShutDownMachine` - Shutdown machine
- `TurnOnMachine` - Turn on machine
- `ApplyMachineWriteback` - Apply machine writeback
- `DiscardMachineWriteback` - Discard machine writeback

#### VM Management Actions (6)
- `ChangeVmCpus` - Change VM CPU count
- `ChangeVmRam` - Change VM RAM
- `ChangeVmDrivesConnection` - Change VM drives connection
- `ChangeVmBiosBootMode` - Change VM BIOS boot mode
- `VncRemoteConnectToVm` - VNC remote connect to VM
- `ConfigureNetworkBridge` - Configure network bridge
- `StartVm` - Start VM
- `ResetVm` - Reset VM
- `StopVm` - Stop VM

#### Image Management Actions (18)
- `CreateImage` - Create new image
- `StartImageBackup` - Start image backup
- `StartImageRestore` - Start image restore
- `StartVhdImageImport` - Start VHD image import
- `StartImageImport` - Start image import
- `StartImageCopy` - Start image copy
- `CancelImageCopy` - Cancel image copy
- `CancelImageRestore` - Cancel image restore
- `CancelVhdImageImport` - Cancel VHD image import
- `CancelImageImport` - Cancel image import
- `RenameImage` - Rename image
- `IncreaseImageVolume` - Increase image volume
- `ChangeImageType` - Change image type
- `ChangeImageDefaultSnapshot` - Change image default snapshot
- `ChangeImageAdSettings` - Change image AD settings
- `SetDefaultImage` - Set default image
- `UnsetDefaultImage` - Unset default image
- `LockImageSnapshot` - Lock image snapshot
- `UnlockImageSnapshot` - Unlock image snapshot
- `DeleteImageSnapshot` - Delete image snapshot
- `DeleteImage` - Delete image

#### Array Management Actions (10)
- `CreateStripe` - Create stripe
- `AttachDrive` - Attach drive
- `ReplaceDrive` - Replace drive
- `DetachDrive` - Detach drive
- `BringDriveOnline` - Bring drive online
- `BringDriveOffline` - Bring drive offline
- `RemoveArray` - Remove array
- `ExportArray` - Export array
- `RunArrayTrim` - Run array trim
- `ResumeArrayTrim` - Resume array trim
- `SuspendArrayTrim` - Suspend array trim
- `CancelArrayTrim` - Cancel array trim

#### Network Device Actions (2)
- `StartAddingNewNicForImage` - Start adding new NIC for image
- `CancelAddingNewNicForImage` - Cancel adding new NIC for image

#### Toolchain Actions (1)
- `SetToolchainVmMac` - Set toolchain VM MAC

#### Scheduling Actions (12)
- `AddScheduledMachineAction` - Add scheduled machine action
- `RemoveScheduledMachineAction` - Remove scheduled machine action
- `ExcludeScheduledMachineActionOccurrences` - Exclude scheduled action occurrences
- `ChangeScheduledMachineActionType` - Change scheduled action type
- `ChangeScheduledMachineActionTime` - Change scheduled action time
- `AddScheduledMachineBootState` - Add scheduled machine boot state
- `RemoveScheduledMachineBootState` - Remove scheduled machine boot state
- `ExcludeScheduledMachineBootStateOccurrences` - Exclude scheduled boot state occurrences
- `ChangeScheduledMachineBootStateTime` - Change scheduled boot state time
- `ChangeScheduledMachineBootStateOverrides` - Change scheduled boot state overrides
- `ChangeScheduledMachineBootStatePreActions` - Change scheduled boot state pre-actions
- `ChangeScheduledMachineBootStatePostActions` - Change scheduled boot state post-actions

#### Behavior Management Actions (6)
- `AddScheduledBehavior` - Add scheduled behavior
- `AssignMachineBehavior` - Assign machine behavior
- `UnassignMachineBehavior` - Unassign machine behavior
- `RenameScheduledBehavior` - Rename scheduled behavior
- `DeleteScheduledBehavior` - Delete scheduled behavior
- `ChangeSchedulerMinDelayBetweenExecutionStarts` - Change scheduler min delay
- `ChangeSchedulerActiveExecutionsLimit` - Change scheduler active executions limit
- `CopyAllScheduledEntries` - Copy all scheduled entries

### 4.2 Activity Log Usage

**Pattern:**
```csharp
// Log activity
await _activityLogService.LogAsync(
    userId: currentUser.Id,
    action: ActivityLogAction.CreateMachine,
    machineId: machine.Id,
    description: $"Created machine {machine.Name}"
);

// Broadcast via SignalR
await _hubContext.Clients.All.SendAsync("activity_log_created", activityLog);
```

---

## 5. Hosted Services & Background Tasks

### 5.1 Hosted Service Implementation

**Location**: `VAjPvb50r74n0fjCaYe/n3LAEr5kZTrGDgLgmvS.cs`

**Class**: `n3LAEr5kZTrGDgLgmvS` implements `IHostedService` and `IDisposable`

**Purpose**: Background service for scheduled tasks and periodic operations

**Registration**:
```csharp
services.AddSingleton<IHostedService, n3LAEr5kZTrGDgLgmvS>();
```

**Key Responsibilities:**
- Scheduled machine actions execution
- Scheduled boot state management
- Periodic system health checks
- Machine connection state monitoring
- Writeback cleanup
- Snapshot management

### 5.2 Background Task Patterns

#### Pattern 1: Periodic Task
```csharp
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    while (!stoppingToken.IsCancellationRequested)
    {
        // Execute task
        await DoWorkAsync();
        
        // Wait for interval
        await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
    }
}
```

#### Pattern 2: Scheduled Task
```csharp
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    while (!stoppingToken.IsCancellationRequested)
    {
        // Get scheduled tasks
        var scheduledTasks = await GetScheduledTasksAsync();
        
        // Execute tasks
        foreach (var task in scheduledTasks)
        {
            if (task.ShouldExecuteNow())
            {
                await ExecuteTaskAsync(task);
            }
        }
        
        // Wait for next check
        await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
    }
}
```

---

## 6. Configuration & Environment Variables

### 6.1 Configuration Sources

**ASP.NET Core Configuration:**
1. `appsettings.json` - Base configuration
2. `appsettings.{Environment}.json` - Environment-specific configuration
3. Environment variables - Override configuration values
4. Command-line arguments - Override configuration values

### 6.2 Known Configuration Keys

#### Database Configuration
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Database=ggrock;Username=ggrock;Password=password"
  }
}
```

#### License Configuration
```json
{
  "License": {
    "Key": "base64-encoded-license-key"
  }
}
```

#### JWT Configuration
```json
{
  "Jwt": {
    "Secret": "jwt-secret-key",
    "Issuer": "GgRock",
    "Audience": "GgRock",
    "ExpirationMinutes": 60
  }
}
```

#### Serilog Configuration
```json
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Verbose",
      "Override": {
        "Microsoft": "Warning",
        "System": "Information"
      }
    },
    "WriteTo": [
      {
        "Name": "Console"
      },
      {
        "Name": "GrafanaLoki",
        "Args": {
          "Uri": "http://localhost:3100"
        }
      }
    ]
  }
}
```

#### CORS Configuration
```json
{
  "Cors": {
    "AllowedOrigins": [
      "http://localhost:4200",
      "https://app.ggrock.com"
    ]
  }
}
```

#### Boot Configuration
```json
{
  "BootConfiguration": {
    "GgRockBoot": true,
    "EnableLockDownEfi": false,
    "SecureBootLockDownEfiUrl": "https://media.ggleap.com/ggrock/secure-boot/LockDown.efi"
  }
}
```

### 6.3 Environment Variables

**ASP.NET Core Environment:**
- `ASPNETCORE_ENVIRONMENT` - Environment name (Development, Staging, Production)

**Custom Environment Variables:**
- Not explicitly visible in decompiled code
- May be used for secrets (connection strings, API keys)

**Recommendations:**
- Use environment variables for all secrets
- Document all required environment variables
- Provide `.env.example` file
- Use configuration providers (Azure Key Vault, AWS Secrets Manager)

---

## 7. DTOs and Serialization

### 7.1 DTO Namespaces

**Domain DTOs:**
- `GgRock.Domain.SerializableTypes.*` - Domain-specific DTOs
- `GgRock.Domain.SerializableTypes.ActivityLogs` - Activity log DTOs
- `GgRock.Domain.SerializableTypes.FeatureToggles` - Feature toggle DTOs
- `GgRock.Domain.SerializableTypes.Toolchain` - Toolchain DTOs

**Client DTOs:**
- `GgRock.SerializableTypes.Client.*` - Client-side DTOs
- `GgRock.SerializableTypes.Client.Dtos` - General client DTOs
- `GgRock.SerializableTypes.Client.Dtos.Images.Models` - Image DTOs
- `GgRock.SerializableTypes.Client.Dtos.Machines` - Machine DTOs

### 7.2 Serialization Configuration

**JSON Serialization:**
- Uses `System.Text.Json` (default in .NET 6)
- May use `Newtonsoft.Json` for compatibility
- Configured in `Startup.ConfigureServices`

**SignalR Serialization:**
- Uses `System.Text.Json` for SignalR messages
- Configured via `JsonHubProtocolOptions`

### 7.3 DTO Patterns

#### Pattern 1: Request DTO
```csharp
public class CreateMachineDto
{
    public string Name { get; set; }
    public MachineType Type { get; set; }
    public string MacAddress { get; set; }
    public Guid? ImageId { get; set; }
}
```

#### Pattern 2: Response DTO
```csharp
public class MachineDto
{
    public Guid Id { get; set; }
    public string Name { get; set; }
    public MachineType Type { get; set; }
    public MachineState State { get; set; }
    public string MacAddress { get; set; }
    public Guid? ImageId { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
```

#### Pattern 3: Progress DTO
```csharp
public class ProgressDto
{
    public Guid OperationId { get; set; }
    public double Progress { get; set; } // 0-100
    public string Status { get; set; }
    public string Message { get; set; }
}
```

---

## Summary

This detailed analysis provides comprehensive information about:

1. **SignalR Events**: 30+ events with detailed descriptions
2. **Service Layer**: Interface definitions and implementation patterns
3. **Error Handling**: Exception types and handling patterns
4. **Activity Logs**: 119 different activity log actions
5. **Hosted Services**: Background task implementation
6. **Configuration**: Configuration sources and keys
7. **DTOs**: Serialization and DTO patterns

**Key Insights:**
- Extensive use of SignalR for real-time updates
- Comprehensive activity logging (119 actions)
- Background services for scheduled tasks
- Well-structured service layer with interfaces
- Standard error handling patterns

**Recommendations:**
- Document all SignalR events in API documentation
- Add XML documentation to service interfaces
- Implement global exception handler
- Document all configuration keys
- Create DTO documentation

---

*Detailed component analysis generated from decompiled GgRock.Api codebase*

