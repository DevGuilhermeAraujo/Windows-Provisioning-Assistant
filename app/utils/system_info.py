"""
Coleta de informações detalhadas do sistema para Dashboard e Relatórios.
"""

import socket
import platform
import os
import json
import logging
from app.utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")


def get_current_hostname() -> str:
    return socket.gethostname()


def get_windows_version() -> str:
    return platform.version()


def get_full_system_info() -> dict:
    """Coleta informações completas do sistema via PowerShell."""
    info = {
        "hostname": get_current_hostname(),
        "windows_version": get_windows_version(),
        "username": os.getenv("USERNAME", ""),
        "cpu": "", "ram_gb": "", "model": "",
        "serial": "", "domain": "", "ip": "", "dns_servers": "", "gateway": "", "adapter": "",
    }
    try:
        ps = """
        $cs = Get-CimInstance Win32_ComputerSystem
        $os = Get-CimInstance Win32_OperatingSystem
        $bios = Get-CimInstance Win32_BIOS
        $cfg = Get-NetIPConfiguration | Where-Object { $_.IPv4Address -ne $null } | Select-Object -First 1
        $ip = if ($cfg) { $cfg.IPv4Address.IPAddress } else { "" }
        $gateway = if ($cfg -and $cfg.IPv4DefaultGateway) { $cfg.IPv4DefaultGateway.NextHop } else { "" }
        $dns = if ($cfg -and $cfg.DNSServer) { ($cfg.DNSServer.ServerAddresses -join ', ') } else { "" }
        $adapter = if ($cfg) { $cfg.InterfaceAlias } else { "" }
        @{
            Model       = $cs.Model
            Manufacturer = $cs.Manufacturer
            RAM         = [math]::Round($cs.TotalPhysicalMemory/1GB, 1)
            CPU         = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name
            Serial      = $bios.SerialNumber
            Domain      = $cs.Domain
            IP          = $ip
            Gateway     = $gateway
            DnsServers  = $dns
            Adapter     = $adapter
            WinCaption  = $os.Caption
            WinBuild    = $os.BuildNumber
        } | ConvertTo-Json
        """
        result = run_powershell(ps)
        if result["success"] and result["output"]:
            data = json.loads(result["output"])
            info.update({
                "model":      data.get("Model", ""),
                "manufacturer": data.get("Manufacturer", ""),
                "ram_gb":     str(data.get("RAM", "")),
                "cpu":        data.get("CPU", ""),
                "serial":     data.get("Serial", ""),
                "domain":     data.get("Domain", ""),
                "ip":         data.get("IP", ""),
                "gateway":    data.get("Gateway", ""),
                "dns_servers": data.get("DnsServers", ""),
                "adapter":    data.get("Adapter", ""),
                "win_caption": data.get("WinCaption", ""),
                "win_build":  data.get("WinBuild", ""),
            })
    except Exception as e:
        logger.warning(f"[SystemInfo] Erro ao coletar info do sistema: {e}")
    return info


def get_network_adapters() -> list:
    """Retorna adaptadores de rede ativos."""
    try:
        cmd = ("Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | "
               "Select-Object Name,InterfaceDescription,Status | ConvertTo-Json")
        result = run_powershell(cmd)
        if result["success"] and result["output"]:
            data = json.loads(result["output"])
            if isinstance(data, dict):
                data = [data]
            return data
    except Exception as e:
        logger.warning(f"[SystemInfo] Erro ao listar adaptadores: {e}")
    return []


def get_adapter_ip_info(adapter_name: str) -> dict:
    """Retorna detalhes de IP de um adaptador específico."""
    try:
        cmd = (f"Get-NetIPAddress -InterfaceAlias '{adapter_name}' -AddressFamily IPv4 "
               f"| Select-Object IPAddress,PrefixLength | ConvertTo-Json")
        result = run_powershell(cmd)
        if result["success"] and result["output"]:
            return json.loads(result["output"])
    except Exception:
        pass
    return {}
