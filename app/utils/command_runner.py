import subprocess
import logging


def run_powershell(command: str, timeout: int = 30) -> dict:
    """
    Executa um comando PowerShell e captura stdout e stderr.
    Retorna um dicionário com 'success', 'output' e 'error'.
    """
    # Monta o comando usando powershell.exe com execução irrestrita
    ps_command = [
        "powershell.exe",
        "-ExecutionPolicy", "Bypass",
        "-NonInteractive",
        "-Command", command
    ]

    try:
        result = subprocess.run(
            ps_command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",      # Evita crash com chars especiais
            timeout=timeout        # Timeout customizável
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 0:
            # Log apenas se houver saída relevante
            if stdout:
                _log_info(f"[PS] OK: {stdout[:200]}")
            return {"success": True, "output": stdout, "error": None}
        else:
            # Se não houver stderr, tentamos pegar o stdout como erro (comum em winget)
            err = stderr if stderr else stdout
            _log_error(f"[PS] Erro (código {result.returncode}): {err[:300]}")
            return {"success": False, "output": stdout, "error": err}

    except subprocess.TimeoutExpired:
        msg = f"PowerShell excedeu o tempo limite ({timeout}s)."
        _log_error(f"[PS] {msg}")
        return {"success": False, "output": "", "error": msg}
    except FileNotFoundError:
        msg = "powershell.exe não encontrado. Verifique sua instalação do Windows."
        _log_error(f"[PS] {msg}")
        return {"success": False, "output": "", "error": msg}
    except Exception as e:
        _log_error(f"[PS] Falha inesperada: {e}")
        return {"success": False, "output": "", "error": str(e)}


def _log_info(msg: str):
    """Log de info sem riscos de reentrada na GUI."""
    try:
        logging.getLogger("WindowsProvisioningAssistant").info(msg)
    except Exception:
        pass


def _log_error(msg: str):
    """Log de erro sem riscos de reentrada na GUI."""
    try:
        logging.getLogger("WindowsProvisioningAssistant").error(msg)
    except Exception:
        pass
