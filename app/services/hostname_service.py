import logging
from ..utils.command_runner import run_powershell
from ..utils.validators import validate_hostname

logger = logging.getLogger("WindowsProvisioningAssistant")

def rename_computer(new_name: str):
    """
    Altera o nome do computador (hostname).
    Requer reinicialização para surtir efeito.
    """
    # 1. Validar nome
    if not validate_hostname(new_name):
        msg = f"Nome do computador inválido: '{new_name}'. Use letras, números e hífens (máx 15 chars)."
        logger.error(f"[Hostname] {msg}")
        return {
            "task_name": "Renomear Computador",
            "success": False,
            "message": msg,
            "details": {"new_name": new_name},
            "executed_commands": [],
            "errors": [msg]
        }
    
    # 2. Executar comando PowerShell
    cmd = f"Rename-Computer -NewName '{new_name}' -Force"
    logger.info(f"[Hostname] Tentando renomear computador para: {new_name}")
    
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = f"Computador renomeado com sucesso para '{new_name}'. Uma reinicialização é necessária."
        logger.info(f"[Hostname] {msg}")
        return {
            "task_name": "Renomear Computador",
            "success": True,
            "message": msg,
            "details": {"new_name": new_name, "reboot_required": True},
            "executed_commands": [cmd],
            "errors": []
        }
    else:
        msg = f"Falha ao renomear computador para '{new_name}'."
        logger.error(f"[Hostname] {msg}: {result['error']}")
        return {
            "task_name": "Renomear Computador",
            "success": False,
            "message": msg,
            "details": {"new_name": new_name},
            "executed_commands": [cmd],
            "errors": [result["error"]]
        }
