import logging
from app.utils.command_runner import run_powershell

logger = logging.getLogger("WindowsProvisioningAssistant")

def run_cleanup():
    """Limpa arquivos temporários, cache do sistema e lixeira."""
    logger.info("[Cleanup] Iniciando limpeza de sistema...")
    
    ps_script = """
    # 1. Limpar Temp do Windows
    Remove-Item -Path "C:\\Windows\\Temp\\*" -Recurse -Force -ErrorAction SilentlyContinue
    # 2. Limpar Temp do Usuário
    Remove-Item -Path "$env:TEMP\\*" -Recurse -Force -ErrorAction SilentlyContinue
    # 3. Limpar Cache do Prefetch
    Remove-Item -Path "C:\\Windows\\Prefetch\\*" -Recurse -Force -ErrorAction SilentlyContinue
    # 4. Esvaziar Lixeira
    Clear-RecycleBin -Force -ErrorAction SilentlyContinue
    """
    
    result = run_powershell(ps_script)
    
    if result["success"]:
        msg = "Limpeza de sistema concluída."
        logger.info(f"[Cleanup] {msg}")
        return {
            "task_name": "Limpeza de Sistema",
            "success": True,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": []
        }
    else:
        msg = "Erro parcial durante a limpeza de sistema."
        logger.warning(f"[Cleanup] {msg}")
        return {
            "task_name": "Limpeza de Sistema",
            "success": False,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": [result["error"]]
        }

def remove_bloatware():
    """Remove aplicativos pré-instalados desnecessários do Windows (ex: Notícias, Clima)."""
    logger.info("[Cleanup] Removendo bloatware...")
    
    ps_script = """
    $apps = @('Microsoft.BingNews', 'Microsoft.BingWeather', 'Microsoft.ZuneVideo', 'Microsoft.ZuneMusic')
    foreach ($app in $apps) {
        Get-AppxPackage -Name $app -AllUsers | Remove-AppxPackage -ErrorAction SilentlyContinue
    }
    """
    
    result = run_powershell(ps_script)
    
    if result["success"]:
        msg = "Remoção de bloatware concluída."
        logger.info(f"[Cleanup] {msg}")
        return {
            "task_name": "Remover Bloatware",
            "success": True,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": []
        }
    else:
        msg = "Erro ao remover alguns aplicativos pré-instalados."
        logger.error(f"[Cleanup] {msg}")
        return {
            "task_name": "Remover Bloatware",
            "success": False,
            "message": msg,
            "executed_commands": [ps_script],
            "errors": [result["error"]]
        }
