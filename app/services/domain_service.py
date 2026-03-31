import logging
from ..utils.command_runner import run_powershell
from ..utils.validators import validate_domain

def join_domain(domain_name: str, username: str, password: str):
    """
    Adiciona o computador ao domínio Active Directory.
    Requer credenciais e reinicialização.
    """
    logger = logging.getLogger("WindowsProvisioningAssistant")
    
    # 1. Validar domínio
    if not validate_domain(domain_name):
        msg = f"Domínio corporativo inválido: '{domain_name}'."
        logger.error(msg)
        return {"success": False, "message": msg}
    
    logger.info(f"Tentando adicionar ao domínio: {domain_name} como usuário {username}")
    
    # Script PowerShell com Credential
    # -Credential $(New-Object System.Management.Automation.PSCredential ...)
    ps_cmd = f"""
    $secpasswd = ConvertTo-SecureString '{password}' -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential ('{username}', $secpasswd)
    Add-Computer -DomainName '{domain_name}' -Credential $credential -Force -ErrorAction Stop
    """
    
    result = run_powershell(ps_cmd)
    
    if result["success"]:
        msg = f"Computador adicionado com sucesso ao domínio '{domain_name}'. Uma reinicialização é necessária."
        logger.info(msg)
        return {"success": True, "message": msg, "reboot_required": True}
    else:
        # Tenta sanitizar o erro para não mostrar o log por razões de segurança em certos casos
        # mas aqui nós queremos o log completo para diagnóstico.
        msg = f"Erro ao adicionar ao domínio: {result['error']}"
        logger.error(msg)
        return {"success": False, "message": msg}
