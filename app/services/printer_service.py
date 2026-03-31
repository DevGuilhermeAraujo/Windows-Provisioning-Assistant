import logging
from ..utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")

def list_printers():
    """Lista todas as impressoras instaladas no sistema."""
    logger.info("[Impressora] Listando impressoras...")
    cmd = "Get-Printer | Select-Object Name, PrinterStatus, PortName | ConvertTo-Json"
    
    result = run_powershell(cmd)
    
    if result["success"] and result["output"]:
        import json
        try:
            return json.loads(result["output"])
        except:
            return []
    return []

def add_network_printer(printer_name: str, ip: str, driver_name: str = "Generic / Text Only"):
    """Adiciona uma impressora de rede via IP."""
    logger.info(f"[Impressora] Adicionando impressora {printer_name} em {ip}...")
    
    # 1. Cria porta TCP/IP
    # 2. Adiciona impressora
    ps_script = f"""
    Add-PrinterPort -Name '{ip}' -PrinterHostAddress '{ip}' -ErrorAction SilentlyContinue
    Add-Printer -Name '{printer_name}' -DriverName '{driver_name}' -PortName '{ip}' -ErrorAction Stop
    """
    
    result = run_powershell(ps_script)
    
    if result["success"]:
        msg = f"Impressora {printer_name} adicionada com sucesso."
        logger.info(f"[Impressora] {msg}")
        return {
            "task_name": f"Adicionar Impressora {printer_name}",
            "success": True,
            "message": msg,
            "details": {"output": result["output"]},
            "executed_commands": [ps_script],
            "errors": []
        }
    else:
        msg = f"Falha ao adicionar impressora {printer_name} em {ip}."
        logger.error(f"[Impressora] {msg}")
        return {
            "task_name": f"Adicionar Impressora {printer_name}",
            "success": False,
            "message": msg,
            "details": {},
            "executed_commands": [ps_script],
            "errors": [result["error"]]
        }

def remove_printer(printer_name: str):
    """Remove uma impressora pelo nome."""
    logger.info(f"[Impressora] Removendo impressora {printer_name}...")
    cmd = f"Remove-Printer -Name '{printer_name}'"
    
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = f"Impressora {printer_name} removida."
        logger.info(f"[Impressora] {msg}")
        return {
            "task_name": f"Remover Impressora {printer_name}",
            "success": True,
            "message": msg,
            "executed_commands": [cmd],
            "errors": []
        }
    else:
        msg = f"Erro ao remover impressora {printer_name}."
        logger.error(f"[Impressora] {msg}")
        return {
            "task_name": f"Remover Impressora {printer_name}",
            "success": False,
            "message": msg,
            "executed_commands": [cmd],
            "errors": [result["error"]]
        }
