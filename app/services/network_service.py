import logging
from ..utils.command_runner import run_powershell
from ..utils.validators import validate_ip, validate_mask

def set_dhcp(adapter_name: str):
    """Define o adaptador para obter IP automaticamente via DHCP."""
    logger = logging.getLogger("WindowsProvisioningAssistant")
    logger.info(f"Configurando DHCP em: {adapter_name}")
    
    # 1. Habilitar DHCP no IP
    # cmd1 = f"Set-NetIPInterface -InterfaceAlias '{adapter_name}' -DHCP Enabled"
    # 2. Habilitar DHCP no DNS
    # cmd2 = f"Set-DnsClientServerAddress -InterfaceAlias '{adapter_name}' -ResetServerAddresses"
    
    # Combinando comandos em um bloco PowerShell
    ps_script = f"""
    Set-NetIPInterface -InterfaceAlias '{adapter_name}' -DHCP Enabled -ErrorAction Stop
    Set-DnsClientServerAddress -InterfaceAlias '{adapter_name}' -ResetServerAddresses -ErrorAction Stop
    """
    
    result = run_powershell(ps_script)
    if result["success"]:
        msg = f"DHCP habilitado com sucesso em '{adapter_name}'."
        logger.info(msg)
        return {"success": True, "message": msg}
    else:
        msg = f"Falha ao configurar DHCP: {result['error']}"
        logger.error(msg)
        return {"success": False, "message": msg}

def set_static_ip(adapter_name: str, ip: str, mask: str, gateway: str = None, dns_servers: list = None):
    """Define IP estático, máscara, gateway e DNS para um adaptador."""
    logger = logging.getLogger("WindowsProvisioningAssistant")
    
    # Validações básicas
    if not validate_ip(ip) or not validate_mask(mask):
        return {"success": False, "message": "IP ou Máscara inválidos."}
    
    logger.info(f"Configurando IP estático {ip} em: {adapter_name}")
    
    # Script PowerShell para remover IP atual (se houver), definir novo e configurar DNS
    # O comando New-NetIPAddress falha se já houver um IP configurado que não seja DHCP
    # O comando Remove-NetIPAddress limpa o estado.
    
    dns_str = ""
    if dns_servers:
        # Formata lista de DNS: "8.8.8.8", "8.8.4.4" -> "'8.8.8.8', '8.8.4.4'"
        dns_str = ",".join([f"'{d}'" for d in dns_servers if validate_ip(d)])

    ps_script = f"""
    # 1. Desabilita DHCP
    Set-NetIPInterface -InterfaceAlias '{adapter_name}' -DHCP Disabled -ErrorAction SilentlyContinue
    
    # 2. Remove IPs IPv4 existentes para evitar conflitos (exclui loopback)
    Get-NetIPAddress -InterfaceAlias '{adapter_name}' -AddressFamily IPv4 | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue
    
    # 3. Adiciona novo endereço
    $params = @{{
        InterfaceAlias = '{adapter_name}'
        IPAddress = '{ip}'
        PrefixLength = {mask_to_prefix(mask)}
    }}
    if ('{gateway}') {{ $params.DefaultGateway = '{gateway}' }}
    
    New-NetIPAddress @params -ErrorAction Stop
    """
    
    if dns_str:
        ps_script += f"\nSet-DnsClientServerAddress -InterfaceAlias '{adapter_name}' -ServerAddresses ({dns_str}) -ErrorAction Stop"

    result = run_powershell(ps_script)
    if result["success"]:
        msg = f"Configuração de IP estático aplicada em '{adapter_name}'."
        logger.info(msg)
        return {"success": True, "message": msg}
    else:
        msg = f"Erro ao aplicar IP estático: {result['error']}"
        logger.error(msg)
        return {"success": False, "message": msg}

def mask_to_prefix(mask: str) -> int:
    """Converte máscara decimal (255.255.255.0) para prefixo CIDR (24)."""
    try:
        import ipaddress
        return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
    except:
        return 24 # Fallback padrão
