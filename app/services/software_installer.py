"""Serviço de instalação de softwares via winget."""

import logging
from app.utils.command_runner import run_powershell
from app.config import settings

logger = logging.getLogger("WindowsProvisioningAssistant")


def is_winget_available() -> bool:
    """Verifica se o winget está disponível no sistema."""
    result = run_powershell("winget --version")
    return result.get("success", False)


def install_package(package_id: str) -> dict:
    """Instala um pacote via winget pelo seu ID (ex: Google.Chrome).
    Retorna sucesso/falha, stdout/stderr, e comando executado.
    """
    logger.info(f"[Software] Instalando pacote: {package_id}")
    if not is_winget_available():
        msg = "winget não encontrado. Instale o App Installer pela Microsoft Store."
        logger.error(f"[Software] {msg}")
        return {
            "success": False,
            "stdout": "",
            "stderr": msg,
            "command": "winget --version"
        }

    # Comando base para instalação com aceite de termos
    cmd = f'winget install --id "{package_id}" --silent --accept-package-agreements --accept-source-agreements'
    result = run_powershell(cmd, timeout=900)
    
    success = result.get("success", False)
    if success:
        logger.info(f"[Software] Instalação concluída: {package_id}")
    else:
        logger.error(f"[Software] Erro na instalação de {package_id}")

    return {
        "success": success,
        "stdout": result.get("output", ""),
        "stderr": result.get("error", ""),
        "command": cmd
    }


def install_multiple(packages: list[str]) -> dict:
    """Instala uma lista de pacotes (passando os IDs)."""
    results = {}
    all_success = True
    
    for pkg_id in packages:
        res = install_package(pkg_id)
        results[pkg_id] = res
        if not res["success"]:
            all_success = False
            
    return {
        "success": all_success,
        "details": results
    }


def list_installed_packages() -> list[str]:
    """Retorna uma lista de IDs de pacotes instalados via winget."""
    if not is_winget_available():
        return []
        
    cmd = "winget list"
    result = run_powershell(cmd, timeout=30)
    if not result.get("success", False):
        return []
        
    lines = result.get("output", "").split('\n')
    installed_ids = []
    
    # Simple parsing to extract the ID column (usually the second column)
    # This is a naive parsing since winget list output is fixed-width
    for line in lines[2:]:
        if len(line.strip()) > 0:
            parts = line.split()
            if len(parts) >= 2:
                # The ID could be parts[1] or parts[-2] depending on name length
                # An easier way is to check for '.' which signifies an ID
                for p in parts:
                    if '.' in p and not p.replace('.', '').isdigit():
                        installed_ids.append(p)
                        break
                        
    return list(set(installed_ids))
