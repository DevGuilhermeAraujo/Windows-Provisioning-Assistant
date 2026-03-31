import socket
import logging
from .command_runner import run_powershell

def get_current_hostname():
    """Retorna o nome atual do computador."""
    return socket.gethostname()

def get_network_adapters():
    """Retorna uma lista de interfaces de rede ativas (Ethernet/Wi-Fi)."""
    logger = logging.getLogger("WindowsProvisioningAssistant")
    # Comando PowerShell para pegar interfaces físicas
    cmd = "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object Name, InterfaceDescription, Status | ConvertTo-Json"
    
    result = run_powershell(cmd)
    if result["success"] and result["output"]:
        import json
        try:
            adapters = json.loads(result["output"])
            # Se retornar apenas um objeto, transforma em lista
            if isinstance(adapters, dict):
                adapters = [adapters]
            return adapters
        except Exception as e:
            logger.error(f"Erro ao parsear adaptadores de rede: {e}")
            return []
    return []

def get_adapter_ip_info(adapter_name):
    """Retorna detalhes de IP de um adaptador específico."""
    cmd = f"Get-NetIPAddress -InterfaceAlias '{adapter_name}' -AddressFamily IPv4 | Select-Object IPAddress, PrefixLength | ConvertTo-Json"
    result = run_powershell(cmd)
    if result["success"] and result["output"]:
        import json
        try:
            return json.loads(result["output"])
        except:
            return None
    return None
