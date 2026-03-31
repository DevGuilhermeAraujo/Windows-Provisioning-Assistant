"""
Scanner de rede com ping paralelo e leitura da tabela ARP.
Identifica IPs ocupados e sugerem IPs livres na subrede.
"""

import subprocess
import ipaddress
import socket
import logging
import concurrent.futures
from typing import List, Dict

from ..config import settings

logger = logging.getLogger("WindowsProvisioningAssistant")


def ping_host(ip: str, timeout: float = None) -> bool:
    """Faz um único ping e retorna True se o host responder."""
    t = timeout or settings.SCAN_TIMEOUT
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(int(t * 1000)), str(ip)],
            capture_output=True, text=True, timeout=t + 1
        )
        return result.returncode == 0
    except Exception:
        return False


def resolve_hostname(ip: str) -> str:
    """Tenta resolver o hostname de um IP, retorna string vazia se falhar."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


def get_arp_table() -> Dict[str, str]:
    """Lê a tabela ARP do Windows e retorna {ip: mac}."""
    result: Dict[str, str] = {}
    try:
        out = subprocess.run(
            ["arp", "-a"], capture_output=True, text=True, timeout=5
        ).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].count(".") == 3:
                ip = parts[0].strip()
                mac = parts[1].strip() if len(parts) > 1 else ""
                result[ip] = mac
    except Exception as e:
        logger.warning(f"[Scanner] Erro ao ler tabela ARP: {e}")
    return result


def scan_network(network_cidr: str,
                 on_progress=None,
                 on_found=None) -> Dict:
    """
    Faz scan completo de uma subrede CIDR.
    Retorna dicionário com IPs ocupados, livres e sugestões.

    Args:
        network_cidr: ex '192.168.1.0/24'
        on_progress:  callback(percent: int)
        on_found:     callback(ip: str, is_up: bool)
    """
    try:
        network = ipaddress.IPv4Network(network_cidr, strict=False)
    except ValueError as e:
        logger.error(f"[Scanner] CIDR inválido: {e}")
        return {"error": str(e)}

    hosts = list(network.hosts())
    total = len(hosts)
    if total == 0:
        return {"error": "Rede sem hosts."}

    # Lê ARP primeiro (mais rápido que ping)
    arp = get_arp_table()

    occupied: List[str] = []
    free: List[str] = []
    scanned = 0

    def check(ip_obj):
        nonlocal scanned
        ip = str(ip_obj)
        is_up = ip in arp or ping_host(ip)
        hostname = resolve_hostname(ip) if is_up else ""
        scanned += 1
        if on_progress:
            on_progress(int(scanned / total * 100))
        if on_found:
            on_found(ip, is_up, hostname)
        return ip, is_up, hostname

    results = []
    max_workers = min(settings.SCAN_THREADS, total)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check, h): h for h in hosts}
        for f in concurrent.futures.as_completed(futures):
            try:
                results.append(f.result())
            except Exception:
                pass

    results.sort(key=lambda x: ipaddress.IPv4Address(x[0]))

    for ip, is_up, hostname in results:
        if is_up:
            occupied.append({"ip": ip, "hostname": hostname,
                             "mac": arp.get(ip, "")})
        else:
            free.append(ip)

    # Sugerir últimos 50 IPs livres do range (mais prováveis para estações novas)
    suggestions = [ip for ip in free[-50:] if ip not in [o["ip"] for o in occupied]]

    return {
        "network": network_cidr,
        "total_hosts": total,
        "occupied": occupied,
        "free": free,
        "suggestions": suggestions[:20],
        "scan_complete": True,
    }


def detect_local_network() -> Dict:
    """Detecta a rede local atual do computador."""
    try:
        # Obtém IP local via PowerShell
        result = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass",
             "-Command",
             "Get-NetIPAddress -AddressFamily IPv4 | "
             "Where-Object { $_.PrefixOrigin -ne 'WellKnown' } | "
             "Select-Object IPAddress, PrefixLength | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            import json
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for entry in data:
                ip = entry.get("IPAddress", "")
                prefix = entry.get("PrefixLength", 24)
                if ip and not ip.startswith("127.") and not ip.startswith("169."):
                    network = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
                    return {
                        "ip": ip,
                        "prefix": prefix,
                        "cidr": str(network),
                        "gateway": str(list(network.hosts())[0]),
                    }
    except Exception as e:
        logger.warning(f"[Scanner] Falha ao detectar rede local: {e}")
    return {"ip": "", "prefix": 24, "cidr": "", "gateway": ""}
