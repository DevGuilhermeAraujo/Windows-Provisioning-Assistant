import logging
from app.utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")

def set_timezone(timezone: str = "E. South America Standard Time"):
    """
    Define o fuso horário do sistema.
    Ex: "E. South America Standard Time" para Brasília.
    """
    logger.info(f"[Time] Definindo fuso horário para: {timezone}...")
    cmd = f"tzutil /s '{timezone}'"
    
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = f"Fuso horário ajustado para '{timezone}'."
        logger.info(f"[Time] {msg}")
        return {
            "task_name": "Definir Fuso Horário",
            "success": True,
            "message": msg,
            "executed_commands": [cmd],
            "errors": []
        }
    else:
        msg = f"Erro ao definir fuso horário para '{timezone}'."
        logger.error(f"[Time] {msg}")
        return {
            "task_name": "Definir Fuso Horário",
            "success": False,
            "message": msg,
            "executed_commands": [cmd],
            "errors": [result["error"]]
        }

def sync_ntp(ntp_server: str = "pool.ntp.org"):
    """Sincroniza o relógio do sistema com um servidor NTP."""
    logger.info(f"[Time] Sincronizando com NTP: {ntp_server}...")
    
    ps_script = f"""
    w32tm /config /manualpeerlist:'{ntp_server},0x1' /syncfromflags:manual /reliable:yes /update
    w32tm /resync
    """
    
    result = run_powershell(ps_script)
    
    if result["success"]:
        msg = "Sincronização de horário concluída."
        logger.info(f"[Time] {msg}")
        return {
            "task_name": f"Sincronizar NTP ({ntp_server})",
            "success": True,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": []
        }
    else:
        msg = f"Falha na sincronização NTP com {ntp_server}."
        logger.error(f"[Time] {msg}")
        return {
            "task_name": f"Sincronizar NTP ({ntp_server})",
            "success": False,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": [result["error"]]
        }
