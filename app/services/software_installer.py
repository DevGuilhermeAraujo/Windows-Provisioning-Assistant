"""Serviço de instalação de softwares via winget."""

import logging
import json
from app.utils.command_runner import run_powershell
from app.config import settings

logger = logging.getLogger("WindowsProvisioningAssistant")


def _check_winget() -> bool:
    """Verifica se o winget está disponível no sistema."""
    result = run_powershell("winget --version")
    return result["success"]


def repair_winget_sources():
    """Tenta resetar as fontes do winget para resolver problemas de download."""
    logger.warning("[Software] Detectado problema de fonte. Tentando resetar fontes do winget...")
    run_powershell("winget source reset --force")
    run_powershell("winget source update")

def install_software(package_id: str, package_name: str) -> dict:
    """Instala um pacote via winget pelo seu ID."""
    logger.info(f"[Software] Instalando: {package_name} ({package_id})")
    if not _check_winget():
        msg = "winget não encontrado. Instale o App Installer pela Microsoft Store."
        logger.error(f"[Software] {msg}")
        return {"task_name": f"Instalar {package_name}", "success": False,
                "message": msg, "errors": [msg], "executed_commands": []}

    # Tenta com locale pt-BR e via fonte winget para evitar avisos de MS Store
    cmd = f'winget install --id "{package_id}" --source winget --silent --accept-package-agreements --accept-source-agreements --locale pt-BR'
    result = run_powershell(cmd, timeout=600)
    
    # Se falhar especificamente por não achar o instalador (comum quando o locale pt-BR não está no manifesto)
    # ou se for erro de fonte, tentamos o comando padrão (sem locale e sem fonte fixa)
    if not result["success"]:
        # Se for erro de idioma ou fonte, tentamos o comando mais genérico
        logger.info(f"[Software] Tentando modo de compatibilidade para {package_name}...")
        cmd_fallback = f'winget install --id "{package_id}" --silent --accept-package-agreements --accept-source-agreements'
        result = run_powershell(cmd_fallback, timeout=600)
        
        # Se ainda falhar, tenta o reparo de fontes e uma última vez
        if not result["success"]:
            repair_winget_sources()
            logger.info(f"[Software] Retentando instalação final de {package_name}...")
            result = run_powershell(cmd_fallback, timeout=600)

    success = result["success"]
    if success:
        msg = f"{package_name} instalado/atualizado com sucesso."
        logger.info(f"[Software] {msg}")
    else:
        msg = f"Erro ao instalar {package_name}. Verifique sua conexão ou se o app já está em uso."
        logger.error(f"[Software] {msg}: {result['error']}")
    
    return {
        "task_name": f"Instalar {package_name}", "success": success,
        "message": msg, "errors": [] if success else [result["error"]],
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
        try:
            return json.loads(result["output"])
        except Exception:
            pass
    return []
