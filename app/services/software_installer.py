"""Serviço de instalação de softwares via winget."""

import logging
from app.utils.command_runner import run_powershell
from app.config import settings

logger = logging.getLogger("WindowsProvisioningAssistant")


def _check_winget() -> bool:
    """Verifica se o winget está disponível no sistema."""
    result = run_powershell("winget --version")
    return result["success"]


def install_software(package_id: str, package_name: str) -> dict:
    """Instala um pacote via winget pelo seu ID."""
    logger.info(f"[Software] Instalando: {package_name} ({package_id})")
    if not _check_winget():
        msg = "winget não encontrado. Instale o App Installer pela Microsoft Store."
        logger.error(f"[Software] {msg}")
        return {"task_name": f"Instalar {package_name}", "success": False,
                "message": msg, "errors": [msg], "executed_commands": []}

    cmd = f'winget install --id "{package_id}" --silent --accept-package-agreements --accept-source-agreements'
    result = run_powershell(cmd)
    msg = (f"{package_name} instalado com sucesso."
           if result["success"] else f"Erro ao instalar {package_name}: {result['error']}")
    if result["success"]:
        logger.info(f"[Software] {msg}")
    else:
        logger.error(f"[Software] {msg}")
    return {
        "task_name": f"Instalar {package_name}", "success": result["success"],
        "message": msg, "errors": [] if result["success"] else [result["error"]],
        "executed_commands": [cmd], "details": {"package_id": package_id},
    }


def install_multiple(packages: list) -> dict:
    """Instala uma lista de softwares. packages = lista de nomes do settings.WINGET_PACKAGES."""
    results = []
    all_success = True
    for name in packages:
        pkg_id = settings.WINGET_PACKAGES.get(name)
        if not pkg_id:
            logger.warning(f"[Software] Pacote desconhecido: {name}")
            continue
        res = install_software(pkg_id, name)
        results.append(res)
        if not res["success"]:
            all_success = False
    msg = "Todos os softwares instalados." if all_success else "Alguns softwares falharam na instalação."
    return {
        "task_name": "Instalar Softwares", "success": all_success,
        "message": msg, "details": {"results": results},
        "executed_commands": [], "errors": [r["message"] for r in results if not r["success"]],
    }


def list_installed() -> list:
    """Lista softwares instalados via winget."""
    result = run_powershell("winget list --source winget | ConvertTo-Csv | ConvertFrom-Csv | ConvertTo-Json")
    if result["success"] and result["output"]:
        import json
        try:
            return json.loads(result["output"])
        except Exception:
            pass
    return []
