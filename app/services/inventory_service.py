"""Servico de Coleta de Inventario Corporativo via PowerShell."""

import logging
from app.utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")


def _run_ps_cmd(cmd: str, default: str = "N/A"):
    """Utilitario para rodar comandos PS simples."""
    try:
        res = run_powershell(cmd, timeout=15)
        if res.get("success") and res.get("output"):
            out = res["output"].strip()
            return out if out else default
        return default
    except Exception as e:
        logger.error(f"[Inventory] Erro no comando '{cmd}': {str(e)}")
        return default


def get_hostname() -> str:
    return _run_powershell_oneliner("(Get-CimInstance Win32_ComputerSystem).Name")


def get_serial_number() -> str:
    return _run_powershell_oneliner("(Get-CimInstance Win32_BIOS).SerialNumber")


def get_manufacturer_model() -> str:
    man = _run_powershell_oneliner("(Get-CimInstance Win32_ComputerSystem).Manufacturer")
    mod = _run_powershell_oneliner("(Get-CimInstance Win32_ComputerSystem).Model")
    return f"{man} {mod}".replace("N/A", "").strip() or "N/A"


def get_windows_version() -> str:
    capt = _run_powershell_oneliner("(Get-CimInstance Win32_OperatingSystem).Caption")
    build = _run_powershell_oneliner("(Get-CimInstance Win32_OperatingSystem).BuildNumber")
    if capt != "N/A":
        return f"{capt} (Build {build})"
    return "N/A"


def get_cpu_info() -> str:
    return _run_powershell_oneliner("(Get-CimInstance Win32_Processor).Name")


def get_ram_info() -> str:
    ram_bytes = _run_powershell_oneliner("(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory")
    try:
        gb = round(int(ram_bytes) / (1024**3), 2)
        return f"{gb} GB"
    except (ValueError, TypeError):
        return "N/A"


def get_disk_info() -> str:
    cmd = 'Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID, FreeSpace, Size | ForEach-Object { "$($_.DeviceID) - Free: $([math]::Round($_.FreeSpace / 1GB, 2)) GB / $([math]::Round($_.Size / 1GB, 2)) GB" }'
    res = run_powershell(cmd)
    if res.get("success") and res.get("output"):
        return res["output"].strip().replace("\n", " | ")
    return "N/A"


def get_mac_addresses() -> str:
    cmd = 'Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True" | Select-Object -ExpandProperty MACAddress'
    res = run_powershell(cmd)
    if res.get("success") and res.get("output"):
        return res["output"].strip().replace("\n", " | ")
    return "N/A"


def get_network_info() -> dict:
    ip = _run_powershell_oneliner('(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "(Loopback|Pseudo)" } | Select-Object -First 1).IPAddress')
    gw = _run_powershell_oneliner('(Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Select-Object -First 1).NextHop')
    dns = _run_powershell_oneliner('(Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "Loopback" } | Select-Object -ExpandProperty ServerAddresses) -join ", "')
    
    return {
        "ip": ip,
        "gateway": gw,
        "dns": dns
    }


def get_domain_status() -> str:
    domain = _run_powershell_oneliner("(Get-CimInstance Win32_ComputerSystem).Domain")
    role = _run_powershell_oneliner("(Get-CimInstance Win32_ComputerSystem).DomainRole")
    # Roles common: 0=Standalone Workstation, 1=Member Workstation, 2=Standalone Server, 3=Member Server
    # 4=Backup Domain Controller, 5=Primary Domain Controller
    if str(role) in ["1", "3", "4", "5"]:
        return f"Joined: {domain}"
    elif str(role) in ["0", "2"]:
        return f"Workgroup: {domain}"
    return domain


def get_full_inventory() -> dict:
    logger.info("[Inventory] Coletando informacoes completas de inventario...")
    net = get_network_info()
    return {
        "hostname": get_hostname(),
        "serial_number": get_serial_number(),
        "model": get_manufacturer_model(),
        "os_version": get_windows_version(),
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "disk": get_disk_info(),
        "mac_addresses": get_mac_addresses(),
        "network": net,
        "domain_status": get_domain_status(),
    }


def _run_powershell_oneliner(cmd: str):
    return _run_ps_cmd(cmd)
