"""Serviço de gerenciamento do Microsoft Defender (Antivírus)."""

import logging
from app.utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")

def get_defender_status() -> dict:
    """Retorna o status atual do Microsoft Defender."""
    cmd = "Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled, AntivirusSignatureLastUpdated, AMServiceEnabled | ConvertTo-Json"
    result = run_powershell(cmd)
    if result["success"] and result["output"]:
        import json
        try:
            return json.loads(result["output"])
        except Exception:
            pass
    return {}

def update_defender() -> dict:
    """Atualiza as definições de vírus do Microsoft Defender."""
    logger.info("[Defender] Atualizando assinaturas de vírus...")
    cmd = "Update-MpSignature"
    result = run_powershell(cmd, timeout=300)
    msg = "Definições atualizadas com sucesso." if result["success"] else f"Erro ao atualizar: {result['error']}"
    return {"success": result["success"], "message": msg}

def run_quick_scan() -> dict:
    """Executa uma verificação rápida do Microsoft Defender."""
    logger.info("[Defender] Iniciando verificação rápida...")
    cmd = "Start-MpScan -ScanType QuickScan"
    # Scan pode demorar, mas não queremos travar por horas. Vamos deixar rodar.
    # Nota: No PowerShell, Start-MpScan é síncrono por padrão.
    result = run_powershell(cmd, timeout=900) # 15 min max
    msg = "Verificação rápida concluída." if result["success"] else f"Erro no scan: {result['error']}"
    return {"success": result["success"], "message": msg}
