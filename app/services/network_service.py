import logging
from app.utils.command_runner import run_powershell
from app.utils.validators import validate_ip, validate_mask

logger = logging.getLogger("WindowsProvisioningAssistant")

def set_dhcp(adapter_name: str):
    """Define o adaptador para obter IP automaticamente via DHCP."""
    logger.info(f"[Rede] Configurando DHCP em: {adapter_name}...")
    
    ps_script = f"""
    Set-NetIPInterface -InterfaceAlias '{adapter_name}' -DHCP Enabled -ErrorAction Stop
    Set-DnsClientServerAddress -InterfaceAlias '{adapter_name}' -ResetServerAddresses -ErrorAction Stop
    """
    
    result = run_powershell(ps_script)
    
    if result["success"]:
        msg = f"DHCP habilitado com sucesso em '{adapter_name}'."
        logger.info(f"[Rede] {msg}")
        return {
            "task_name": "Configurar DHCP",
            "success": True,
            "message": msg,
            "details": {"adapter": adapter_name},
            "executed_commands": [ps_script],
            "errors": []
        }
    else:
        msg = f"Falha ao configurar DHCP em '{adapter_name}'."
        logger.error(f"[Rede] {msg}: {result['error']}")
        return {
            "task_name": "Configurar DHCP",
            "success": False,
            "message": msg,
            "details": {"adapter": adapter_name},
            "executed_commands": [ps_script],
            "errors": [result["error"]]
        }

def set_static_ip(adapter_name: str, ip: str, mask: str, gateway: str = None, dns_servers: list = None):
    """Define IP estático para um adaptador."""
    # Validações básicas
    if not validate_ip(ip) or not validate_mask(mask):
        msg = "IP ou Máscara inválidos."
        logger.error(f"[Rede] {msg}")
        return {
            "task_name": "Configurar IP Estático",
            "success": False,
            "message": msg,
            "details": {"ip": ip, "mask": mask},
            "executed_commands": [],
            "errors": [msg]
        }
    
    logger.info(f"[Rede] Configurando IP Estático {ip} em {adapter_name}...")
    
    dns_str = ""
    if dns_servers:
        dns_str = ",".join([f"'{d}'" for d in dns_servers if validate_ip(d)])

    prefix = mask_to_prefix(mask)
    ps_script = f"""
    Set-NetIPInterface -InterfaceAlias '{adapter_name}' -DHCP Disabled -ErrorAction SilentlyContinue
    Get-NetIPAddress -InterfaceAlias '{adapter_name}' -AddressFamily IPv4 | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue
    
    $params = @{{
        InterfaceAlias = '{adapter_name}'
        IPAddress = '{ip}'
        PrefixLength = {prefix}
    }}
    if ('{gateway}') {{ $params.DefaultGateway = '{gateway}' }}
    
    New-NetIPAddress @params -ErrorAction Stop
    """
    
    if dns_str:
        ps_script += f"\nSet-DnsClientServerAddress -InterfaceAlias '{adapter_name}' -ServerAddresses ({dns_str}) -ErrorAction Stop"

    result = run_powershell(ps_script)
    
    if result["success"]:
        msg = f"IP Estático {ip} aplicado em '{adapter_name}'."
        logger.info(f"[Rede] {msg}")
        return {
            "task_name": "Configurar IP Estático",
            "success": True,
            "message": msg,
            "details": {"adapter": adapter_name, "ip": ip, "mask": mask},
            "executed_commands": [ps_script],
            "errors": []
        }
    else:
        msg = f"Falha ao configurar IP Estático em '{adapter_name}'."
        logger.error(f"[Rede] {msg}: {result['error']}")
        return {
            "task_name": "Configurar IP Estático",
            "success": False,
            "message": msg,
            "details": {"adapter": adapter_name, "ip": ip, "mask": mask},
            "executed_commands": [ps_script],
            "errors": [result["error"]]
        }

def mask_to_prefix(mask: str) -> int:
    """Converte máscara decimal para prefixo CIDR."""
    try:
        import ipaddress
        return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
    except:
        return 24
