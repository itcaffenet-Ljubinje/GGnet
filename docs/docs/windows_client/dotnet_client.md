# .NET Windows Client

The .NET Windows Client is the primary implementation of the ggnet2 Windows Client using .NET 6.0/8.0.

## Project Structure

```
ggnet2-toolchain/
├── src/
│   ├── Program.cs                 # Main entry point
│   ├── Service/
│   │   └── ToolchainService.cs    # Windows Service
│   ├── SignalR/
│   │   └── HubConnection.cs        # SignalR client
│   ├── Registry/
│   │   └── RegistryManager.cs     # Registry operations
│   ├── WMI/
│   │   └── WMIManager.cs          # WMI operations
│   └── Models/
│       └── Messages.cs            # Message types
├── ggnet2-toolchain.csproj
└── appsettings.json
```

## Main Entry Point

**Program.cs:**
```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace ggnet2.toolchain
{
    class Program
    {
        static void Main(string[] args)
        {
            CreateHostBuilder(args).Build().Run();
        }

        static IHostBuilder CreateHostBuilder(string[] args) =>
            Host.CreateDefaultBuilder(args)
                .UseWindowsService()
                .ConfigureServices((hostContext, services) =>
                {
                    services.AddHostedService<ToolchainService>();
                });
        }
    }
}
```

## Windows Service

**Service/ToolchainService.cs:**
```csharp
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace ggnet2.toolchain.Service
{
    public class ToolchainService : BackgroundService
    {
        private readonly ILogger<ToolchainService> _logger;
        private readonly HubConnection _hubConnection;

        public ToolchainService(
            ILogger<ToolchainService> logger,
            HubConnection hubConnection)
        {
            _logger = logger;
            _hubConnection = hubConnection;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            await ConnectToHub(stoppingToken);
            
            while (!stoppingToken.IsCancellationRequested)
            {
                await SendStatusUpdate();
                await Task.Delay(30000, stoppingToken); // 30 seconds
            }
        }

        private async Task ConnectToHub(CancellationToken cancellationToken)
        {
            try
            {
                await _hubConnection.StartAsync(cancellationToken);
                _logger.LogInformation("Connected to SignalR hub");
                
                await RegisterClient();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to connect to SignalR hub");
            }
        }

        private async Task RegisterClient()
        {
            var clientInfo = new ClientInfo
            {
                ClientId = GetClientId(),
                Mac = GetMacAddress(),
                Ip = GetIpAddress(),
                Name = Environment.MachineName
            };

            await _hubConnection.SendAsync("Register", clientInfo);
        }

        private async Task SendStatusUpdate()
        {
            var status = new StatusUpdate
            {
                ClientId = GetClientId(),
                Status = "online",
                Uptime = GetUptime(),
                Speed = GetNetworkSpeed()
            };

            await _hubConnection.SendAsync("StatusUpdate", status);
        }
    }
}
```

## SignalR Client

**SignalR/HubConnection.cs:**
```csharp
using Microsoft.AspNetCore.SignalR.Client;
using Microsoft.Extensions.Configuration;

namespace ggnet2.toolchain.SignalR
{
    public class HubConnection
    {
        private readonly HubConnection _connection;

        public HubConnection(IConfiguration configuration)
        {
            var serverUrl = configuration["Server:Url"];
            _connection = new HubConnectionBuilder()
                .WithUrl($"{serverUrl}/hubs/clients")
                .WithAutomaticReconnect()
                .Build();

            SetupHandlers();
        }

        private void SetupHandlers()
        {
            _connection.On<Command>("Command", async (command) =>
            {
                await HandleCommand(command);
            });

            _connection.On<Broadcast>("Broadcast", (message) =>
            {
                HandleBroadcast(message);
            });

            _connection.On<string>("Disconnect", (reason) =>
            {
                HandleDisconnect(reason);
            });
        }

        public async Task StartAsync(CancellationToken cancellationToken)
        {
            await _connection.StartAsync(cancellationToken);
        }

        public async Task SendAsync(string method, object arg)
        {
            await _connection.SendAsync(method, arg);
        }

        private async Task HandleCommand(Command command)
        {
            switch (command.CommandType)
            {
                case "rename_pc":
                    await RenamePC(command.Params);
                    break;
                case "inject_env":
                    await InjectEnvironmentVariables(command.Params);
                    break;
                case "registry_script":
                    await ApplyRegistryScript(command.Params);
                    break;
            }
        }
    }
}
```

## Registry Manager

**Registry/RegistryManager.cs:**
```csharp
using Microsoft.Win32;

namespace ggnet2.toolchain.Registry
{
    public class RegistryManager
    {
        public void SetRegistryValue(string keyPath, string valueName, object value)
        {
            using (var key = Registry.LocalMachine.OpenSubKey(keyPath, true))
            {
                if (key != null)
                {
                    key.SetValue(valueName, value);
                }
            }
        }

        public object GetRegistryValue(string keyPath, string valueName)
        {
            using (var key = Registry.LocalMachine.OpenSubKey(keyPath))
            {
                if (key != null)
                {
                    return key.GetValue(valueName);
                }
            }
            return null;
        }

        public void ApplyRegistryScript(string scriptPath)
        {
            var process = new System.Diagnostics.Process
            {
                StartInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "reg.exe",
                    Arguments = $"import {scriptPath}",
                    UseShellExecute = false,
                    CreateNoWindow = true
                }
            };
            process.Start();
            process.WaitForExit();
        }

        public void RenamePC(string newName)
        {
            SetRegistryValue(
                @"SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName",
                "ComputerName",
                newName
            );
        }

        public void InjectEnvironmentVariables(Dictionary<string, string> envVars)
        {
            foreach (var envVar in envVars)
            {
                Environment.SetEnvironmentVariable(envVar.Key, envVar.Value, EnvironmentVariableTarget.Machine);
            }
        }
    }
}
```

## WMI Manager

**WMI/WMIManager.cs:**
```csharp
using System.Management;

namespace ggnet2.toolchain.WMI
{
    public class WMIManager
    {
        public string GetSystemInfo()
        {
            var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_ComputerSystem");
            foreach (ManagementObject obj in searcher.Get())
            {
                return obj["Name"].ToString();
            }
            return null;
        }

        public string GetMacAddress()
        {
            var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_NetworkAdapter WHERE NetConnectionStatus = 2");
            foreach (ManagementObject obj in searcher.Get())
            {
                return obj["MACAddress"].ToString();
            }
            return null;
        }

        public Dictionary<string, object> GetPerformanceMetrics()
        {
            var metrics = new Dictionary<string, object>();
            
            var cpuSearcher = new ManagementObjectSearcher("SELECT * FROM Win32_Processor");
            foreach (ManagementObject obj in cpuSearcher.Get())
            {
                metrics["CPUUsage"] = obj["LoadPercentage"];
            }

            var memorySearcher = new ManagementObjectSearcher("SELECT * FROM Win32_OperatingSystem");
            foreach (ManagementObject obj in memorySearcher.Get())
            {
                metrics["TotalMemory"] = obj["TotalVisibleMemorySize"];
                metrics["FreeMemory"] = obj["FreePhysicalMemory"];
            }

            return metrics;
        }
    }
}
```

## Message Types

**Models/Messages.cs:**
```csharp
namespace ggnet2.toolchain.Models
{
    public class ClientInfo
    {
        public string ClientId { get; set; }
        public string Mac { get; set; }
        public string Ip { get; set; }
        public string Name { get; set; }
    }

    public class StatusUpdate
    {
        public string ClientId { get; set; }
        public string Status { get; set; }
        public string Uptime { get; set; }
        public string Speed { get; set; }
        public string Sent { get; set; }
        public string Received { get; set; }
    }

    public class Command
    {
        public string CommandType { get; set; }
        public Dictionary<string, object> Params { get; set; }
    }

    public class Broadcast
    {
        public string Message { get; set; }
    }
}
```

## Configuration

**appsettings.json:**
```json
{
  "Server": {
    "Url": "http://localhost:8000"
  },
  "Client": {
    "ClientId": "auto-generated",
    "UpdateInterval": 30000,
    "HeartbeatInterval": 60000
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

## Installation

### Install as Windows Service

```bash
# Build project
dotnet build

# Install service
sc create ggnet2-toolchain binPath="C:\path\to\ggnet2-toolchain.exe"
sc start ggnet2-toolchain
```

### Uninstall Service

```bash
sc stop ggnet2-toolchain
sc delete ggnet2-toolchain
```

## Development Notes

- Windows Service requires administrator privileges
- SignalR connection requires network access to server
- Registry operations require appropriate permissions
- WMI queries may require elevated privileges
- Status updates are sent every 30 seconds
- Heartbeat is sent every 60 seconds

## To-Do

- [ ] Add client authentication
- [ ] Implement client update mechanism
- [ ] Add client health monitoring
- [ ] Implement client remote desktop
- [ ] Add client performance metrics
- [ ] Implement client logging

