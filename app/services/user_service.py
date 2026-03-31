import logging
from ..utils.command_runner import run_powershell
from ..utils.validators import validate_username

def create_local_admin(username: str, password: str):
    """Cria um novo usuário local e o torna administrador."""
    logger = logging.getLogger("WindowsProvisioningAssistant")
    
    # 1. Validar nome de usuário
    if not validate_username(username):
        msg = f"Nome de usuário inválido: '{username}'."
        logger.error(msg)
        return {"success": False, "message": msg}
    
    logger.info(f"Tentando criar usuário local: {username} como administrador")
    
    # Script PowerShell para criar usuário e adicionar ao grupo de administradores
    # O group name 'Administradores' é em PT-BR, mas 'Administrators' é inglês. 
    # Usaremos SIDs para compatibilidade universal se possível, ou o comando PowerShell que detecta automaticamente.
    ps_cmd = f"""
    $secpasswd = ConvertTo-SecureString '{password}' -AsPlainText -Force
    New-LocalUser -Name '{username}' -Password $secpasswd -FullName 'Administrador de Provisionamento' -Description 'Usuário criado pelo Windows Provisioning Assistant' -ErrorAction Stop
    
    # Adicionando ao grupo de administradores (LocalGroup builtin)
    $group = (Get-LocalGroup | Where-Object {{ $_.SID -eq 'S-1-5-32-544' }}).Name
    Add-LocalGroupMember -Group $group -Member '{username}' -ErrorAction Stop
    """
    
    result = run_powershell(ps_cmd)
    
    if result["success"]:
        msg = f"Usuário '{username}' criado com sucesso e adicionado ao grupo de administradores."
        logger.info(msg)
        return {"success": True, "message": msg}
    else:
        msg = f"Falha ao criar usuário administrador: {result['error']}"
        logger.error(msg)
        return {"success": False, "message": msg}
