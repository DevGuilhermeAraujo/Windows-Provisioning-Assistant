"""
Registro central de todas as tarefas de provisionamento disponíveis.
Mapeia identificadores de tarefas para as funções dos serviços correspondentes.
"""

from ..services import (
    hostname_service,
    network_service,
    domain_service,
    user_service,
    software_installer,
    windows_update_service,
    firewall_service,
    bitlocker_service,
    remote_access_service,
    printer_service,
    time_service,
    power_plan_service,
    policies_service,
    cleanup_service
)

# Dicionário que mapeia o ID da tarefa para a função que a executa
# Todas as funções devem seguir o padrão de retorno dict definido no plano v2
TASK_MAP = {
    "hostname":     hostname_service.rename_computer,
    "dhcp":         network_service.set_dhcp,
    "static_ip":    network_service.set_static_ip,
    "domain_join":  domain_service.join_domain,
    "create_user":  user_service.create_local_admin,
    "install_apps": software_installer.install_multiple,
    "win_updates":  windows_update_service.install_updates,
    "firewall_on":  firewall_service.enable_firewall,
    "rdp_on":       remote_access_service.enable_rdp,
    "time_sync":    time_service.sync_ntp,
    "set_timezone": time_service.set_timezone,
    "perf_plan":    power_plan_service.set_high_performance_plan,
    "no_sleep":     power_plan_service.prevent_sleep,
    "telemetry":    policies_service.disable_telemetry,
    "cleanup":      cleanup_service.run_cleanup,
    "debloat":      cleanup_service.remove_bloatware,
    "bitlocker":    bitlocker_service.enable_bitlocker
}

def get_task_function(task_id: str):
    """Retorna a função associada ao ID da tarefa."""
    return TASK_MAP.get(task_id)

def get_available_tasks() -> list:
    """Retorna a lista de todos os IDs de tarefas disponíveis."""
    return list(TASK_MAP.keys())
