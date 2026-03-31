"""Serviço de gerenciamento do Firewall do Windows."""

import logging
from ..utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")


def enable_firewall() -> dict:
    """Ativa o Firewall do Windows em todos os perfis."""
    logger.info("[Firewall] Ativando Firewall do Windows...")
    cmd = "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True"
    result = run_powershell(cmd)
    msg = "Firewall ativado em todos os perfis." if result["success"] else f"Falha: {result['error']}"
    if result["success"]:
        logger.info(f"[Firewall] {msg}")
    else:
        logger.error(f"[Firewall] {msg}")
    return {"task_name": "Ativar Firewall", "success": result["success"],
            "message": msg, "executed_commands": [cmd],
            "errors": [] if result["success"] else [result["error"]], "details": {}}


def disable_firewall() -> dict:
    """DESATIVA o Firewall. Use apenas para diagnóstico."""
    logger.warning("[Firewall] Desativando Firewall — operação de risco!")
    cmd = "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False"
    result = run_powershell(cmd)
    msg = "Firewall desativado." if result["success"] else f"Falha: {result['error']}"
    return {"task_name": "Desativar Firewall", "success": result["success"],
            "message": msg, "executed_commands": [cmd],
            "errors": [] if result["success"] else [result["error"]], "details": {}}


def get_firewall_status() -> dict:
    """Retorna o status atual do Firewall para cada perfil."""
    cmd = "Get-NetFirewallProfile | Select-Object Name,Enabled | ConvertTo-Json"
    result = run_powershell(cmd)
    if result["success"] and result["output"]:
        import json
        try:
            return json.loads(result["output"])
        except Exception:
            pass
    return {}


def allow_rdp_rule() -> dict:
    """Cria regra de entrada para RDP (porta 3389)."""
    logger.info("[Firewall] Criando regra de RDP...")
    cmd = ("New-NetFirewallRule -DisplayName 'WPA-RDP' -Direction Inbound "
           "-Protocol TCP -LocalPort 3389 -Action Allow -Profile Any "
           "-ErrorAction SilentlyContinue")
    result = run_powershell(cmd)
    msg = "Regra de RDP criada." if result["success"] else f"Falha: {result['error']}"
    return {"task_name": "Regra Firewall RDP", "success": result["success"],
            "message": msg, "executed_commands": [cmd],
            "errors": [] if result["success"] else [result["error"]], "details": {}}
