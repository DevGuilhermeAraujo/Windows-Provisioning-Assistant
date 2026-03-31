import ctypes
import sys
import os

def is_admin() -> bool:
    """Verifica se o programa está sendo executado como administrador."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def run_as_admin() -> bool:
    """
    Tenta reiniciar o programa com privilégios de administrador via ShellExecuteW.
    Retorna True se conseguiu elevar, False se foi bloqueado ou falhou.
    """
    if is_admin():
        return True

    python_exe = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", python_exe, f'"{script_path}" {params}', None, 1
        )
        # ShellExecuteW retorna > 32 em caso de sucesso
        if result > 32:
            return True
        else:
            return False
    except Exception:
        return False
