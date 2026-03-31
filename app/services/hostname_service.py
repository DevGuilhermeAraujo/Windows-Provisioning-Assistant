import logging
from ..utils.command_runner import run_powershell
from ..utils.validators import validate_hostname

def rename_computer(new_name: str):
    """
    Altera o nome do computador (hostname).
    Requer reinicialização para surtir efeito.
    """
    logger = logging.getLogger("WindowsProvisioningAssistant")
    
    # 1. Validar nome
    if not validate_hostname(new_name):
        msg = f"Nome do computador inválido: '{new_name}'. Use letras, números e hífens (máx 15 chars)."
        logger.error(msg)
        return {"success": False, "message": msg}
    
    # 2. Executar comando PowerShell
    cmd = f"Rename-Computer -NewName '{new_name}' -Force"
    logger.info(f"Tentando renomear computador para: {new_name}")
    
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = f"Computador renomeado com sucesso para '{new_name}'. Uma reinicialização é necessária."
        logger.info(msg)
        return {"success": True, "message": msg, "reboot_required": True}
    else:
        msg = f"Falha ao renomear computador: {result['error']}"
        logger.error(msg)
        return {"success": False, "message": msg}
