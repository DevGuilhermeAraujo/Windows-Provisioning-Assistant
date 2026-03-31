import logging
from ..utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")

def check_bitlocker_support():
    """Verifica se o sistema suporta BitLocker (presença de TPM)."""
    logger.info("[BitLocker] Verificando compatibilidade...")
    cmd = "Get-Tpm | Select-Object -ExpandProperty TpmPresent"
    
    result = run_powershell(cmd)
    
    if result["success"] and "True" in result["output"]:
        msg = "TPM presente. BitLocker disponível."
        logger.info(f"[BitLocker] {msg}")
        return True
    else:
        logger.warning("[BitLocker] TPM não encontrado ou desabilitado.")
        return False

def enable_bitlocker(drive: str = "C:"):
    """Ativa a criptografia BitLocker na unidade especificada."""
    logger.info(f"[BitLocker] Ativando criptografia na unidade {drive}...")
    
    # Gerar chave de recuperação (Recovery Key)
    # Requer que o TPM esteja pronto
    cmd = f"Enable-BitLocker -MountPoint '{drive}' -EncryptionMethod XtsAes128 -UsedSpaceOnly -TpmProtector"
    
    result = run_powershell(cmd)
    
    if result["success"]:
        msg = f"Criptografia BitLocker iniciada para a unidade {drive}."
        logger.info(f"[BitLocker] {msg}")
        return {
            "task_name": f"Ativar BitLocker {drive}",
            "success": True,
            "message": msg,
            "details": {"output": result["output"]},
            "executed_commands": [cmd],
            "errors": []
        }
    else:
        msg = f"Falha ao ativar BitLocker na unidade {drive}."
        logger.error(f"[BitLocker] {msg}")
        return {
            "task_name": f"Ativar BitLocker {drive}",
            "success": False,
            "message": msg,
            "details": {},
            "executed_commands": [cmd],
            "errors": [result["error"]]
        }

def get_recovery_key(drive: str = "C:"):
    """Recupera a chave de recuperação do BitLocker para a unidade."""
    cmd = f"(Get-BitLockerVolume -MountPoint '{drive}').KeyProtector | Where-Object {{ $_.KeyProtectorType -eq 'RecoveryPassword' }} | Select-Object -ExpandProperty RecoveryPassword"
    
    result = run_powershell(cmd)
    
    if result["success"] and result["output"]:
        return result["output"].strip()
    return None
