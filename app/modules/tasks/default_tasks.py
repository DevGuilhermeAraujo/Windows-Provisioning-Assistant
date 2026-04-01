from __future__ import annotations

from typing import Any

from app.modules.task_base import TaskBase
from app.config import settings
from app.services import (
    cleanup_service,
    firewall_service,
    hostname_service,
    network_service,
    power_plan_service,
    remote_access_service,
    software_installer,
    time_service,
)


def _missing_field_result(task_name: str, missing: list[str]) -> dict[str, Any]:
    msg = f"Campos obrigatorios ausentes no contexto: {', '.join(missing)}"
    return {
        "task_name": task_name,
        "success": False,
        "message": msg,
        "details": {"missing_fields": missing},
        "executed_commands": [],
        "errors": [msg],
    }


class HostnameTask(TaskBase):
    def __init__(self) -> None:
        super().__init__("hostname", "Altera o nome do computador", ["new_hostname"])

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        missing = self.validate_context(context)
        if missing:
            return _missing_field_result(self.name, missing)
        return hostname_service.rename_computer(context["new_hostname"])


class StaticIpTask(TaskBase):
    def __init__(self) -> None:
        super().__init__("static_ip", "Configura IP estatico ou DHCP", ["adapter_name", "use_dhcp"])

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        missing = self.validate_context(context)
        if missing:
            return _missing_field_result(self.name, missing)

        adapter = context["adapter_name"]
        if context.get("use_dhcp"):
            return network_service.set_dhcp(adapter)

        required_static = ["ip", "mask"]
        missing_static = [f for f in required_static if not context.get(f)]
        if missing_static:
            return _missing_field_result(self.name, missing_static)

        dns_servers = [context.get("dns_primary"), context.get("dns_secondary")]
        dns_servers = [d for d in dns_servers if d]
        return network_service.set_static_ip(
            adapter_name=adapter,
            ip=context["ip"],
            mask=context["mask"],
            gateway=context.get("gateway"),
            dns_servers=dns_servers,
        )


class TimeSyncTask(TaskBase):
    def __init__(self) -> None:
        super().__init__("time_sync", "Sincroniza horario NTP", [])

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        return time_service.sync_ntp()


class PerfPlanTask(TaskBase):
    def __init__(self) -> None:
        super().__init__("perf_plan", "Ativa plano de alto desempenho", [])

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if not context.get("enable_high_performance", True):
            msg = "Plano de alta performance desabilitado no contexto."
            return {
                "task_name": self.name,
                "success": True,
                "message": msg,
                "details": {},
                "executed_commands": [],
                "errors": [],
            }
        return power_plan_service.set_high_performance_plan()


class FirewallOnTask(TaskBase):
    def __init__(self) -> None:
        super().__init__("firewall_on", "Ativa firewall", [])

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if not context.get("enable_firewall", True):
            msg = "Ativacao de firewall desabilitada no contexto."
            return {
                "task_name": self.name,
                "success": True,
                "message": msg,
                "details": {},
                "executed_commands": [],
                "errors": [],
            }
        result = firewall_service.enable_firewall()
        return {
            "task_name": self.name,
            "success": bool(result.get("success")),
            "message": result.get("message", ""),
            "details": {},
            "executed_commands": result.get("executed_commands", []),
            "errors": result.get("errors", []),
        }


class RdpOnTask(TaskBase):
    def __init__(self) -> None:
        super().__init__("rdp_on", "Habilita acesso remoto", [])

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if not context.get("enable_rdp", True):
            msg = "Habilitacao de RDP desabilitada no contexto."
            return {
                "task_name": self.name,
                "success": True,
                "message": msg,
                "details": {},
                "executed_commands": [],
                "errors": [],
            }
        return remote_access_service.enable_rdp()


class InstallAppsTask(TaskBase):
    def __init__(self) -> None:
        super().__init__("install_apps", "Instala aplicativos selecionados", [])

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        packages = context.get("install_packages", [])
        if not packages:
            msg = "Nenhum pacote selecionado para instalacao."
            return {
                "task_name": self.name,
                "success": True,
                "message": msg,
                "details": {"packages": []},
                "executed_commands": [],
                "errors": [],
            }
        
        # O contexto deve fornecer os IDs dos pacotes Winget (ex: Google.Chrome)
        result = software_installer.install_multiple(packages)
        success = result.get("success", False)
        msg_out = "Softwares instalados com sucesso!" if success else "Ocorreram erros durante a instalacao dos softwares."
        
        return {
            "task_name": self.name,
            "success": success,
            "message": msg_out,
            "details": result.get("details", {}),
            "executed_commands": [],
            "errors": [] if success else ["Falha em um ou mais pacotes. Veja o log detalhado."],
        }


class CleanupTask(TaskBase):
    def __init__(self) -> None:
        super().__init__("cleanup", "Executa limpeza de sistema", [])

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if not context.get("enable_cleanup", True):
            msg = "Limpeza desabilitada no contexto."
            return {
                "task_name": self.name,
                "success": True,
                "message": msg,
                "details": {},
                "executed_commands": [],
                "errors": [],
            }
        return cleanup_service.run_cleanup()


DEFAULT_TASKS: list[TaskBase] = [
    HostnameTask(),
    StaticIpTask(),
    TimeSyncTask(),
    PerfPlanTask(),
    FirewallOnTask(),
    RdpOnTask(),
    InstallAppsTask(),
    CleanupTask(),
]
