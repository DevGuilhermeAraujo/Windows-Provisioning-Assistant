import logging
from ..utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")

def check_updates():
    """Verifica se há atualizações disponíveis usando o módulo PSWindowsUpdate (se disponível)."""
    logger.info("[Windows Update] Verificando atualizações...")
    # Tenta usar o módulo PSWindowsUpdate ou o comando nativo simplificado
    cmd = "Get-WindowsUpdate -AcceptAll -IgnoreReboot"
    # Nota: Este comando requer que o usuário tenha o módulo PSWindowsUpdate instalado via Install-Module
    # Como fallback, podemos apenas verificar o status do serviço
    
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = "Verificação de atualizações concluída."
        logger.info(f"[Windows Update] {msg}")
        return {
            "task_name": "Verificar Atualizações",
            "success": True,
            "message": msg,
            "details": {"output": result["output"]},
            "executed_commands": [cmd],
            "errors": []
        }
    else:
        msg = "Falha ao verificar atualizações ou módulo PSWindowsUpdate não instalado."
        logger.warning(f"[Windows Update] {msg}")
        return {
            "task_name": "Verificar Atualizações",
            "success": False,
            "message": msg,
            "details": {},
            "executed_commands": [cmd],
            "errors": [result["error"]]
        }

def install_updates():
    """Instala todas as atualizações críticas disponíveis."""
    logger.info("[Windows Update] Iniciando instalação de atualizações críticas...")
    cmd = "Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -AutoReboot"
    
    # Este comando pode demorar muito, idealmente rodar em background ou com timeout longo
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = "Atualizações instaladas com sucesso."
        logger.info(f"[Windows Update] {msg}")
        return {
            "task_name": "Instalar Atualizações",
            "success": True,
            "message": msg,
            "details": {"output": result["output"]},
            "executed_commands": [cmd],
            "errors": []
        }
    else:
        msg = "Erro durante a instalação das atualizações."
        logger.error(f"[Windows Update] {msg}")
        return {
            "task_name": "Instalar Atualizações",
            "success": False,
            "message": msg,
            "details": {},
            "executed_commands": [cmd],
            "errors": [result["error"]]
        }
