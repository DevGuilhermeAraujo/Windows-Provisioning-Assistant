import logging
from app.utils.command_runner import run_powershell
from app.utils.validators import validate_domain

logger = logging.getLogger("WindowsProvisioningAssistant")

def join_domain(domain_name: str, username: str, password: str):
    """
    Adiciona o computador ao domínio Active Directory.
    Requer credenciais e reinicialização.
    """
    # 1. Validar domínio
    if not validate_domain(domain_name):
        msg = f"Domínio corporativo inválido: '{domain_name}'."
        logger.error(f"[Domínio] {msg}")
        return {
            "task_name": "Ingressar no Domínio",
            "success": False,
            "message": msg,
            "details": {"domain": domain_name},
            "executed_commands": [],
            "errors": [msg]
        }
    
    logger.info(f"[Domínio] Tentando adicionar ao domínio: {domain_name} como usuário {username}...")
    
    ps_cmd = f"""
    $secpasswd = ConvertTo-SecureString '{password}' -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential ('{username}', $secpasswd)
    Add-Computer -DomainName '{domain_name}' -Credential $credential -Force -ErrorAction Stop
    """
    
    result = run_powershell(ps_cmd)
    
    if result["success"]:
        msg = f"Computador adicionado com sucesso ao domínio '{domain_name}'. Uma reinicialização é necessária."
        logger.info(f"[Domínio] {msg}")
        return {
            "task_name": "Ingressar no Domínio",
            "success": True,
            "message": msg,
            "details": {"domain": domain_name, "reboot_required": True},
            "executed_commands": [ps_cmd],
            "errors": []
        }
    else:
        msg = f"Falha ao entrar no domínio '{domain_name}' para o usuário '{username}'."
        logger.error(f"[Domínio] {msg}: {result['error']}")
        return {
            "task_name": "Ingressar no Domínio",
            "success": False,
            "message": msg,
            "details": {"domain": domain_name},
            "executed_commands": [ps_cmd],
            "errors": [result["error"]]
        }
