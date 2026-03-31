import ctypes
import sys
import os

def is_admin():
    """Verifica se o programa está sendo executado como administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    """Tenta reiniciar o programa com privilégios de administrador."""
    if is_admin():
        return True
    
    # Obter o executável do Python e os argumentos do script atual
    python_exe = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    
    # Comando PowerShell para iniciar o processo como admin
    # "Start-Process -FilePath '{python_exe}' -ArgumentList '{script_path} {params}' -Verb RunAs"
    try:
        # Usando ShellExecute do Windows para elevar
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", python_exe, f'"{script_path}" {params}', None, 1
        )
        sys.exit(0)
    except Exception as e:
        print(f"Erro ao tentar elevar privilégios: {e}")
        return False
