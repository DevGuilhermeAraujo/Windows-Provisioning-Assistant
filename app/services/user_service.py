import logging
from ..utils.command_runner import run_powershell
from ..utils.validators import validate_username

logger = logging.getLogger("WindowsProvisioningAssistant")

def create_local_admin(username: str, password: str):
    """Cria um novo usuário local e o torna administrador."""
    # 1. Validar nome de usuário
    if not validate_username(username):
        msg = f"Nome de usuário inválido: '{username}'."
        logger.error(f"[Usuário] {msg}")
        return {
            "task_name": "Criar Usuário Local Admin",
            "success": False,
            "message": msg,
            "details": {"username": username},
            "executed_commands": [],
            "errors": [msg]
        }
    
    logger.info(f"[Usuário] Tentando criar usuário local: {username} como administrador...")
    
    ps_cmd = f"""
    $secpasswd = ConvertTo-SecureString '{password}' -AsPlainText -Force
    New-LocalUser -Name '{username}' -Password $secpasswd -FullName 'Administrador de Provisionamento' -Description 'Usuário criado pelo Windows Provisioning Assistant' -ErrorAction Stop
    $group = (Get-LocalGroup | Where-Object {{ $_.SID -eq 'S-1-5-32-544' }}).Name
    Add-LocalGroupMember -Group $group -Member '{username}' -ErrorAction Stop
    """
    
    result = run_powershell(ps_cmd)
    
    if result["success"]:
        msg = f"Usuário '{username}' criado e adicionado ao grupo de administradores."
        logger.info(f"[Usuário] {msg}")
        return {
            "task_name": "Criar Usuário Local Admin",
            "success": True,
            "message": msg,
            "details": {"username": username},
            "executed_commands": [ps_cmd],
            "errors": []
        }
    else:
        msg = f"Falha ao criar usuário administrador '{username}'."
        logger.error(f"[Usuário] {msg}: {result['error']}")
        return {
            "task_name": "Criar Usuário Local Admin",
            "success": False,
            "message": msg,
            "details": {"username": username},
            "executed_commands": [ps_cmd],
            "errors": [result["error"]]
        }
