# Python Windows Client

The Python Windows Client is an alternative implementation of the ggnet2 Windows Client using Python 3.10+.

## Project Structure

```
python_client/
├── src/
│   ├── main.py                 # Main entry point
│   ├── service.py              # Windows Service wrapper
│   ├── websocket_client.py      # WebSocket client
│   ├── registry_manager.py      # Registry operations
│   └── wmi_manager.py          # WMI operations
└── requirements.txt
```

## Main Entry Point

**main.py:**
```python
import sys
import win32serviceutil
import win32service
import servicemanager
from service import ToolchainService

class ToolchainServiceWrapper(win32serviceutil.ServiceFramework):
    _svc_name_ = "ggnet2-toolchain"
    _svc_display_name_ = "ggnet2 Toolchain Service"
    _svc_description_ = "ggnet2 Windows Client Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.service = ToolchainService()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.service.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.service.start()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ToolchainServiceWrapper)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ToolchainServiceWrapper)
```

## Windows Service

**service.py:**
```python
import time
import threading
from websocket_client import WebSocketClient
from registry_manager import RegistryManager
from wmi_manager import WMIManager

class ToolchainService:
    def __init__(self):
        self.running = False
        self.websocket_client = WebSocketClient()
        self.registry_manager = RegistryManager()
        self.wmi_manager = WMIManager()
        self.client_id = self.get_client_id()

    def start(self):
        self.running = True
        self.connect_to_server()
        self.start_status_updates()

    def stop(self):
        self.running = False
        self.websocket_client.disconnect()

    def connect_to_server(self):
        self.websocket_client.connect()
        self.register_client()

    def register_client(self):
        client_info = {
            "client_id": self.client_id,
            "mac": self.wmi_manager.get_mac_address(),
            "ip": self.wmi_manager.get_ip_address(),
            "name": self.wmi_manager.get_computer_name()
        }
        self.websocket_client.send("register", client_info)

    def start_status_updates(self):
        def update_loop():
            while self.running:
                status = self.get_status()
                self.websocket_client.send("status", status)
                time.sleep(30)  # 30 seconds

        thread = threading.Thread(target=update_loop)
        thread.daemon = True
        thread.start()

    def get_status(self):
        return {
            "client_id": self.client_id,
            "status": "online",
            "uptime": self.get_uptime(),
            "speed": self.wmi_manager.get_network_speed()
        }

    def get_client_id(self):
        # Get or generate client ID from registry
        return self.registry_manager.get_client_id()

    def get_uptime(self):
        # Calculate uptime
        return "02:30:45"
```

## WebSocket Client

**websocket_client.py:**
```python
import websockets
import json
import asyncio
from registry_manager import RegistryManager
from wmi_manager import WMIManager

class WebSocketClient:
    def __init__(self):
        self.server_url = "ws://localhost:8000/hubs/clients"
        self.websocket = None
        self.connected = False
        self.registry_manager = RegistryManager()
        self.wmi_manager = WMIManager()

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            await self.setup_handlers()
        except Exception as e:
            print(f"Failed to connect: {e}")

    async def setup_handlers(self):
        async def handle_message():
            while self.connected:
                try:
                    message = await self.websocket.recv()
                    await self.handle_message(message)
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break

        asyncio.create_task(handle_message())

    async def handle_message(self, message):
        data = json.loads(message)
        event = data.get("event")
        payload = data.get("data", {})

        if event == "command":
            await self.handle_command(payload)
        elif event == "broadcast":
            await self.handle_broadcast(payload)

    async def handle_command(self, command_data):
        command_type = command_data.get("command")
        params = command_data.get("params", {})

        if command_type == "rename_pc":
            self.registry_manager.rename_pc(params.get("new_name"))
        elif command_type == "inject_env":
            self.registry_manager.inject_environment_variables(params.get("env_vars", {}))
        elif command_type == "registry_script":
            self.registry_manager.apply_registry_script(params.get("script_path"))

    async def handle_broadcast(self, broadcast_data):
        message = broadcast_data.get("message")
        print(f"Broadcast: {message}")

    async def send(self, event, data):
        if self.connected and self.websocket:
            message = {
                "event": event,
                "data": data
            }
            await self.websocket.send(json.dumps(message))

    def disconnect(self):
        self.connected = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
```

## Registry Manager

**registry_manager.py:**
```python
import winreg
import subprocess
import os

class RegistryManager:
    def get_value(self, key_path, value_name):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except Exception as e:
            print(f"Error getting registry value: {e}")
            return None

    def set_value(self, key_path, value_name, value):
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error setting registry value: {e}")

    def apply_registry_script(self, script_path):
        try:
            subprocess.run(["reg.exe", "import", script_path], check=True)
        except Exception as e:
            print(f"Error applying registry script: {e}")

    def rename_pc(self, new_name):
        key_path = r"SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName"
        self.set_value(key_path, "ComputerName", new_name)

    def inject_environment_variables(self, env_vars):
        for key, value in env_vars.items():
            os.environ[key] = value
            # Set in registry for persistence
            key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
            self.set_value(key_path, key, value)

    def get_client_id(self):
        key_path = r"SOFTWARE\ggnet2"
        client_id = self.get_value(key_path, "ClientID")
        if not client_id:
            import uuid
            client_id = str(uuid.uuid4())
            self.set_value(key_path, "ClientID", client_id)
        return client_id
```

## WMI Manager

**wmi_manager.py:**
```python
import wmi

class WMIManager:
    def __init__(self):
        self.wmi_conn = wmi.WMI()

    def get_computer_name(self):
        for computer in self.wmi_conn.Win32_ComputerSystem():
            return computer.Name

    def get_mac_address(self):
        for adapter in self.wmi_conn.Win32_NetworkAdapter(NetConnectionStatus=2):
            return adapter.MACAddress

    def get_ip_address(self):
        for adapter in self.wmi_conn.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            if adapter.IPAddress:
                return adapter.IPAddress[0]

    def get_network_speed(self):
        for adapter in self.wmi_conn.Win32_NetworkAdapter(NetConnectionStatus=2):
            return f"{adapter.Speed / 1000000}Mbps"

    def get_performance_metrics(self):
        metrics = {}
        
        for processor in self.wmi_conn.Win32_Processor():
            metrics["CPUUsage"] = processor.LoadPercentage

        for os in self.wmi_conn.Win32_OperatingSystem():
            metrics["TotalMemory"] = os.TotalVisibleMemorySize
            metrics["FreeMemory"] = os.FreePhysicalMemory

        return metrics
```

## Requirements

**requirements.txt:**
```txt
websockets>=12.0
pywin32>=305
wmi>=1.5.1
```

## Installation

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install as Windows Service

```bash
# Install service
python main.py install

# Start service
python main.py start

# Stop service
python main.py stop

# Remove service
python main.py remove
```

## Development Notes

- Windows Service requires administrator privileges
- WebSocket connection requires network access to server
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

