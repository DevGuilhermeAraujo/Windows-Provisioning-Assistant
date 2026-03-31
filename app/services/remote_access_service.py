"""Serviço de acesso remoto — habilita RDP e configura regras de firewall."""

import logging
from app.utils.command_runner import run_powershell
from app.services.firewall_service import allow_rdp_rule

logger = logging.getLogger("WindowsProvisioningAssistant")


def enable_rdp() -> dict:
    """Habilita RDP e configura o firewall correspondente."""
    logger.info("[RDP] Habilitando Acesso Remoto...")
    # Tentamos os nomes em Inglês e Português para compatibilidade
    cmds = [
        "Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name 'fDenyTSConnections' -Value 0",
        "Enable-NetFirewallRule -DisplayGroup 'Remote Desktop' -ErrorAction SilentlyContinue",
        "Enable-NetFirewallRule -DisplayGroup 'Área de Trabalho Remota' -ErrorAction SilentlyContinue",
    ]
    errors = []
    executed = []
    for cmd in cmds:
        r = run_powershell(cmd)
        executed.append(cmd)
        # Se for o Enable-NetFirewallRule, não consideramos erro se falhar em um dos idiomas
        if not r["success"] and "Set-ItemProperty" in cmd:
            errors.append(r["error"] or "")

    # Adiciona regra customizada também
    allow_rdp_rule()

    success = len(errors) == 0
    msg = "RDP habilitado com sucesso." if success else f"Erros ao habilitar RDP: {errors}"
    if success:
        logger.info(f"[RDP] {msg}")
    else:
        logger.error(f"[RDP] {msg}")
    return {"task_name": "Habilitar RDP", "success": success, "message": msg,
            "executed_commands": executed, "errors": errors, "details": {}}


def disable_rdp() -> dict:
    """Desabilita RDP."""
    logger.info("[RDP] Desabilitando Acesso Remoto...")
    cmd = ("Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' "
           "-Name 'fDenyTSConnections' -Value 1")
    result = run_powershell(cmd)
    msg = "RDP desabilitado." if result["success"] else f"Falha: {result['error']}"
    return {"task_name": "Desabilitar RDP", "success": result["success"],
            "message": msg, "executed_commands": [cmd],
            "errors": [] if result["success"] else [result["error"]], "details": {}}


def get_rdp_status() -> bool:
    """Retorna True se RDP está habilitado."""
    result = run_powershell(
        "Get-ItemPropertyValue 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' fDenyTSConnections"
    )
    return result["success"] and result["output"].strip() == "0"
