#!/usr/bin/env python3
"""
GGnet Hardware Detection Script

This script runs on the client machine to detect hardware
and report back to the GGnet server.

Usage:
    python3 hardware_detect.py --server http://192.168.1.10:8000
"""
import subprocess
import json
import sys
import argparse
import requests
import re
from typing import Dict, List, Optional


def run_command(cmd: List[str]) -> str:
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout
    except Exception as e:
        print(f"Error running {' '.join(cmd)}: {e}", file=sys.stderr)
        return ""


def detect_cpu() -> Dict[str, any]:
    """Detect CPU information"""
    try:
        # Try lscpu first (Linux)
        output = run_command(["lscpu"])
        if output:
            cpu_model = ""
            cpu_cores = 0
            
            for line in output.split('\n'):
                if "Model name:" in line:
                    cpu_model = line.split(":", 1)[1].strip()
                elif "CPU(s):" in line and "NUMA" not in line:
                    cpu_cores = int(line.split(":", 1)[1].strip())
            
            return {
                "model": cpu_model or "Unknown CPU",
                "cores": cpu_cores or 1
            }
    except:
        pass
    
    # Fallback: try /proc/cpuinfo (Linux)
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            
        cpu_model = ""
        cpu_cores = 0
        
        for line in cpuinfo.split('\n'):
            if "model name" in line:
                cpu_model = line.split(":", 1)[1].strip()
            if "processor" in line:
                cpu_cores += 1
        
        return {
            "model": cpu_model or "Unknown CPU",
            "cores": cpu_cores or 1
        }
    except:
        pass
    
    # Fallback: Unknown
    return {
        "model": "Unknown CPU",
        "cores": 1
    }


def detect_ram() -> int:
    """Detect RAM size in GB"""
    try:
        # Try free -g (Linux)
        output = run_command(["free", "-g"])
        if output:
            for line in output.split('\n'):
                if "Mem:" in line:
                    parts = line.split()
                    return int(parts[1])
    except:
        pass
    
    # Fallback: try /proc/meminfo (Linux)
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if "MemTotal:" in line:
                    kb = int(line.split()[1])
                    return max(1, kb // 1024 // 1024)  # KB to GB
    except:
        pass
    
    return 1  # Fallback


def detect_network_cards() -> List[Dict[str, str]]:
    """Detect network cards"""
    cards = []
    
    try:
        # Try ip link show (Linux)
        output = run_command(["ip", "link", "show"])
        if output:
            current_card = {}
            
            for line in output.split('\n'):
                # Look for interface name
                if ": " in line and not line.startswith(" "):
                    if current_card:
                        cards.append(current_card)
                    
                    parts = line.split(":")
                    if len(parts) >= 2:
                        name = parts[1].strip()
                        if name not in ["lo", "docker0"] and not name.startswith("veth"):
                            current_card = {"name": name}
                
                # Look for MAC address
                elif "link/ether" in line and current_card:
                    mac = line.split()[1]
                    current_card["mac"] = mac
                    current_card["vendor"] = "Unknown"
                    current_card["speed"] = "Unknown"
            
            if current_card:
                cards.append(current_card)
    except:
        pass
    
    # Fallback: try /sys/class/net (Linux)
    if not cards:
        try:
            import os
            net_dir = "/sys/class/net"
            for iface in os.listdir(net_dir):
                if iface in ["lo", "docker0"] or iface.startswith("veth"):
                    continue
                
                mac_file = os.path.join(net_dir, iface, "address")
                if os.path.exists(mac_file):
                    with open(mac_file, "r") as f:
                        mac = f.read().strip()
                        cards.append({
                            "name": iface,
                            "mac": mac,
                            "vendor": "Unknown",
                            "speed": "Unknown"
                        })
        except:
            pass
    
    return cards


def detect_bios_info() -> Dict[str, Optional[str]]:
    """Detect BIOS/UEFI information"""
    info = {
        "manufacturer": None,
        "model": None,
        "serial_number": None,
        "bios_version": None,
        "boot_mode": None,
        "secureboot_enabled": None
    }
    
    try:
        # Try dmidecode (requires root)
        output = run_command(["sudo", "dmidecode", "-t", "system"])
        if output:
            for line in output.split('\n'):
                if "Manufacturer:" in line:
                    info["manufacturer"] = line.split(":", 1)[1].strip()
                elif "Product Name:" in line:
                    info["model"] = line.split(":", 1)[1].strip()
                elif "Serial Number:" in line:
                    info["serial_number"] = line.split(":", 1)[1].strip()
        
        # Get BIOS version
        output = run_command(["sudo", "dmidecode", "-t", "bios"])
        if output:
            for line in output.split('\n'):
                if "Version:" in line:
                    info["bios_version"] = line.split(":", 1)[1].strip()
                    break
    except:
        pass
    
    # Detect boot mode (UEFI vs BIOS)
    try:
        import os
        if os.path.exists("/sys/firmware/efi"):
            info["boot_mode"] = "UEFI"
            
            # Check SecureBoot status
            try:
                with open("/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c", "rb") as f:
                    data = f.read()
                    info["secureboot_enabled"] = data[-1] == 1
            except:
                info["secureboot_enabled"] = None
        else:
            info["boot_mode"] = "BIOS"
            info["secureboot_enabled"] = False
    except:
        pass
    
    return info


def get_primary_mac() -> str:
    """Get primary MAC address"""
    cards = detect_network_cards()
    if cards:
        return cards[0]["mac"]
    return "00:00:00:00:00:00"


def detect_hardware() -> Dict:
    """Detect all hardware information"""
    print("Detecting hardware...", file=sys.stderr)
    
    cpu = detect_cpu()
    ram = detect_ram()
    network_cards = detect_network_cards()
    bios = detect_bios_info()
    
    hardware = {
        "mac_address": get_primary_mac(),
        "manufacturer": bios.get("manufacturer"),
        "model": bios.get("model"),
        "serial_number": bios.get("serial_number"),
        "bios_version": bios.get("bios_version"),
        "cpu_model": cpu["model"],
        "cpu_cores": cpu["cores"],
        "ram_gb": ram,
        "network_cards": network_cards,
        "boot_mode": bios.get("boot_mode"),
        "secureboot_enabled": bios.get("secureboot_enabled")
    }
    
    print(f"Detected: {hardware['manufacturer']} {hardware['model']}", file=sys.stderr)
    print(f"  CPU: {hardware['cpu_model']} ({hardware['cpu_cores']} cores)", file=sys.stderr)
    print(f"  RAM: {hardware['ram_gb']} GB", file=sys.stderr)
    print(f"  MAC: {hardware['mac_address']}", file=sys.stderr)
    print(f"  Boot Mode: {hardware['boot_mode']}", file=sys.stderr)
    
    return hardware


def report_hardware(server_url: str, hardware: Dict) -> bool:
    """Report hardware to GGnet server"""
    try:
        url = f"{server_url}/api/hardware/report"
        print(f"Reporting to: {url}", file=sys.stderr)
        
        response = requests.post(
            url,
            json=hardware,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success: {data['message']}", file=sys.stderr)
            print(f"  Machine ID: {data.get('machine_id')}", file=sys.stderr)
            print(f"  Auto-created: {data.get('auto_created')}", file=sys.stderr)
            return True
        else:
            print(f"✗ Error: {response.status_code} - {response.text}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Failed to report hardware: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="GGnet Hardware Detection"
    )
    parser.add_argument(
        "--server",
        required=True,
        help="GGnet server URL (e.g., http://192.168.1.10:8000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect hardware but don't report to server"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output hardware info as JSON"
    )
    
    args = parser.parse_args()
    
    # Detect hardware
    hardware = detect_hardware()
    
    if args.json:
        print(json.dumps(hardware, indent=2))
        return 0
    
    if args.dry_run:
        print("\n=== Hardware Detection (Dry Run) ===", file=sys.stderr)
        print(json.dumps(hardware, indent=2), file=sys.stderr)
        return 0
    
    # Report to server
    success = report_hardware(args.server, hardware)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

