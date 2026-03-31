import logging
from app.utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")

def set_high_performance_plan():
    """Define o plano de energia como 'Alto Desempenho'."""
    logger.info("[Energia] Definindo plano como Alto Desempenho...")
    
    # Busca o GUID do plano de Alto Desempenho
    cmd = "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = "Plano de energia definido para Alto Desempenho."
        logger.info(f"[Energia] {msg}")
        return {
            "task_name": "Definir Plano (Alto Desempenho)",
            "success": True,
            "message": msg,
            "executed_commands": [cmd],
            "errors": []
        }
    else:
        msg = "Falha ao definir plano de energia. Pode ser necessário criar o esquema."
        logger.error(f"[Energia] {msg}")
        return {
            "task_name": "Definir Plano (Alto Desempenho)",
            "success": False,
            "message": msg,
            "executed_commands": [cmd],
            "errors": [result["error"]]
        }

def prevent_sleep():
    """Configura o sistema para nunca entrar em modo de suspensão quando conectado."""
    logger.info("[Energia] Desabilitando suspensão automática (AC)...")
    
    ps_script = """
    powercfg /x -timeout-ac-sleep 0
    powercfg /x -timeout-ac-display-blank 0
    """
    
    result = run_powershell(ps_script)
    
    if result["success"]:
        msg = "Suspensão desabilitada."
        logger.info(f"[Energia] {msg}")
        return {
            "task_name": "Prevenir Suspensão",
            "success": True,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": []
        }
    else:
        msg = "Erro ao configurar tempos limite de energia."
        logger.error(f"[Energia] {msg}")
        return {
            "task_name": "Prevenir Suspensão",
            "success": False,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": [result["error"]]
        }
