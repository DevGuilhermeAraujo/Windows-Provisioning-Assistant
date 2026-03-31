import subprocess
import logging
import shlex

def run_powershell(command: str):
    """Executa um comando PowerShell e captura a saída."""
    logger = logging.getLogger("WindowsProvisioningAssistant")
    
    # Montar comando PowerShell
    # -ExecutionPolicy Bypass para evitar restrições de script
    # -Command "{command}" para rodar o comando propriamente dito
    ps_command = f'powershell.exe -ExecutionPolicy Bypass -Command "{command}"'
    
    logger.debug(f"Executando PowerShell: {ps_command}")
    
    try:
        # Usando subprocess.run para capturar saída e erros
        result = subprocess.run(
            ps_command, 
            capture_output=True, 
            text=True, 
            encoding='cp850', # Encoding comum no console Windows brasileiro
            shell=True # Shell=True para executar via powershell.exe diretamente
        )
        
        # Captura stdout e stderr
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        if result.returncode == 0:
            if stdout:
                logger.info(f"Saída: {stdout}")
            return {"success": True, "output": stdout, "error": None}
        else:
            logger.error(f"Erro na execução (Código {result.returncode}): {stderr}")
            return {"success": False, "output": stdout, "error": stderr}
            
    except Exception as e:
        logger.error(f"Falha ao executar o comando: {e}")
        return {"success": False, "output": "", "error": str(e)}

def run_powershell_script(script_path: str, args: list = None):
    """Executa um arquivo de script PowerShell (.ps1)."""
    if args is None:
        args = []
    
    params = " ".join([f'"{arg}"' for arg in args])
    command = f"& '{script_path}' {params}"
    return run_powershell(command)
