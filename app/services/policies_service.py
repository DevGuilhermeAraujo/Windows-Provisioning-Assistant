import logging
from ..utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")

def disable_uac():
    """Desabilita o UAC (User Account Control). Apenas para fins de diagnóstico ou ambientes específicos."""
    logger.warning("[Políticas] Desabilitando UAC...")
    
    cmd = "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'EnableLUA' -Value 0"
    
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = "UAC desabilitado. Reinicialização necessária."
        logger.info(f"[Políticas] {msg}")
        return {
            "task_name": "Desabilitar UAC",
            "success": True,
            "message": msg,
            "executed_commands": [cmd],
            "errors": []
        }
    else:
        msg = "Erro ao desabilitar UAC."
        logger.error(f"[Políticas] {msg}")
        return {
            "task_name": "Desabilitar UAC",
            "success": False,
            "message": msg,
            "executed_commands": [cmd],
            "errors": [result["error"]]
        }

def disable_telemetry():
    """Desabilita a telemetria e coleta de dados básicas do Windows."""
    logger.info("[Políticas] Desabilitando telemetria e rastreamento...")
    
    ps_script = """
    # Desabilitar telemetria no Registro
    Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection' -Name 'AllowTelemetry' -Value 0
    # Parar serviços de rastreamento
    Stop-Service -Name DiagTrack -ErrorAction SilentlyContinue
    Set-Service -Name DiagTrack -StartupType Disabled -ErrorAction SilentlyContinue
    """
    
    result = run_powershell(ps_script)
    
    if result["success"]:
        msg = "Telemetria desabilitada."
        logger.info(f"[Políticas] {msg}")
        return {
            "task_name": "Desabilitar Telemetria",
            "success": True,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": []
        }
    else:
        msg = "Erro ao configurar políticas de telemetria."
        logger.error(f"[Políticas] {msg}")
        return {
            "task_name": "Desabilitar Telemetria",
            "success": False,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": [result["error"]]
        }
