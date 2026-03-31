"""Serviço de gerenciamento do Firewall do Windows."""

import logging
from app.utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")


def set_firewall_profile_status(profile: str, enabled: bool) -> dict:
    """Ativa ou desativa um perfil específico do Firewall (Domain, Private, Public)."""
    status_str = "True" if enabled else "False"
    logger.info(f"[Firewall] {'Ativando' if enabled else 'Desativando'} perfil {profile}...")
    cmd = f"Set-NetFirewallProfile -Profile {profile} -Enabled {status_str}"
    result = run_powershell(cmd)
    msg = f"Perfil {profile} {'ativado' if enabled else 'desativado'}." if result["success"] else f"Falha: {result['error']}"
    return {"success": result["success"], "message": msg, "executed_commands": [cmd]}


def enable_firewall() -> dict:
    """Ativa o Firewall do Windows em todos os perfis."""
    return set_firewall_profile_status("Domain,Public,Private", True)


def disable_firewall() -> dict:
    """DESATIVA o Firewall em todos os perfis."""
    return set_firewall_profile_status("Domain,Public,Private", False)


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
