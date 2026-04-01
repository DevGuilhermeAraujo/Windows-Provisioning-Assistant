from __future__ import annotations

from typing import Any


def _pick(gui_inputs: dict[str, Any], profile_data: dict[str, Any], key: str, default: Any = None) -> Any:
    value = gui_inputs.get(key)
    if value is None or (isinstance(value, str) and value.strip() == ""):
        value = profile_data.get(key, default)
    return value


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "sim", "on"}
    return bool(value)


def build_context(gui_inputs: dict, profile_data: dict) -> dict:
    install_packages = gui_inputs.get("install_packages")
    if install_packages is None:
        install_packages = profile_data.get("softwares", [])

    context = {
        "new_hostname": _pick(gui_inputs, profile_data, "new_hostname", ""),
        "adapter_name": _pick(gui_inputs, profile_data, "adapter_name", ""),
        "use_dhcp": _to_bool(_pick(gui_inputs, profile_data, "use_dhcp", False), False),
        "ip": _pick(gui_inputs, profile_data, "ip", ""),
        "mask": _pick(gui_inputs, profile_data, "mask", ""),
        "gateway": _pick(gui_inputs, profile_data, "gateway", ""),
        "dns_primary": _pick(gui_inputs, profile_data, "dns_primary", ""),
        "dns_secondary": _pick(gui_inputs, profile_data, "dns_secondary", ""),
        "enable_rdp": _to_bool(_pick(gui_inputs, profile_data, "enable_rdp", True), True),
        "enable_firewall": _to_bool(_pick(gui_inputs, profile_data, "enable_firewall", True), True),
        "enable_high_performance": _to_bool(_pick(gui_inputs, profile_data, "enable_high_performance", True), True),
        "enable_cleanup": _to_bool(_pick(gui_inputs, profile_data, "enable_cleanup", True), True),
        "install_packages": install_packages if isinstance(install_packages, list) else [],
        "domain_name": _pick(gui_inputs, profile_data, "domain_name", profile_data.get("domain", "")),
        "domain_user": _pick(gui_inputs, profile_data, "domain_user", ""),
        "domain_password": _pick(gui_inputs, profile_data, "domain_password", ""),
    }

    return context
