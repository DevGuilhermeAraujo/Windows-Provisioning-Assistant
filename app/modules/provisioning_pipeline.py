import logging
import time
from typing import Any, Callable

from app.database import db
from app.modules.task_registry import get_task
from app.utils import system_info

logger = logging.getLogger("WindowsProvisioningAssistant")

STRICT = "STRICT"
SAFE = "SAFE"


class ProvisioningPipeline:
    def __init__(self, execution_id: int = None):
        self.execution_id = execution_id
        self.results: list[dict[str, Any]] = []
        self.ordered_tasks: list[str] = [
            "hostname",
            "static_ip",
            "time_sync",
            "perf_plan",
            "firewall_on",
            "rdp_on",
            "install_apps",
            "cleanup",
        ]

    def _emit(self, callbacks: dict, callback_name: str, *args) -> None:
        cb = callbacks.get(callback_name) if callbacks else None
        if callable(cb):
            cb(*args)

    def _sanitize_for_log(self, context: dict[str, Any]) -> dict[str, Any]:
        safe = dict(context)
        if "domain_password" in safe and safe["domain_password"]:
            safe["domain_password"] = "***"
        return safe

    def run(
        self,
        selected_tasks: list[str],
        context: dict[str, Any],
        mode: str,
        callbacks: dict | None = None,
    ) -> dict[str, Any]:
        mode = (mode or SAFE).upper()
        if mode not in {STRICT, SAFE}:
            mode = SAFE

        task_order = [t for t in self.ordered_tasks if t in selected_tasks]
        total_tasks = len(task_order)
        if total_tasks == 0:
            return {
                "execution_id": self.execution_id,
                "status": "EMPTY",
                "success_count": 0,
                "failed_count": 0,
                "total_tasks": 0,
                "results": [],
                "summary": "Nenhuma task selecionada.",
            }

        if not self.execution_id:
            username = system_info.get_full_system_info().get("username", "unknown")
            computer_name = system_info.get_current_hostname()
            self.execution_id = db.start_execution(username, computer_name)

        self.results = []
        success_count = 0
        failed_count = 0
        safe_context = self._sanitize_for_log(context)
        self._emit(callbacks or {}, "on_log", f"Contexto inicial: {safe_context}")

        for index, task_name in enumerate(task_order):
            self._emit(callbacks or {}, "on_task_start", task_name)
            self._emit(
                callbacks or {},
                "on_progress",
                int((index / total_tasks) * 100),
            )
            task = get_task(task_name)

            if not task:
                res = {
                    "task_name": task_name,
                    "success": False,
                    "message": f"Task '{task_name}' nao encontrada.",
                    "details": {},
                    "executed_commands": [],
                    "errors": [f"Task '{task_name}' nao encontrada."],
                }
            else:
                start = time.time()
                try:
                    res = task.run(context)
                except Exception as exc:
                    err = str(exc)
                    res = {
                        "task_name": task_name,
                        "success": False,
                        "message": f"Erro inesperado na task '{task_name}'.",
                        "details": {},
                        "executed_commands": [],
                        "errors": [err],
                    }
                res["duration_ms"] = int((time.time() - start) * 1000)

            db.log_task(
                self.execution_id,
                res.get("task_name", task_name),
                bool(res.get("success")),
                res.get("message", ""),
                "; ".join(res.get("errors", [])),
                res.get("duration_ms", 0),
            )

            self.results.append(res)
            self._emit(callbacks or {}, "on_task_finish", task_name, res)
            self._emit(
                callbacks or {},
                "on_log",
                f"[{task_name}] {'OK' if res.get('success') else 'ERRO'} - {res.get('message', '')}",
            )

            if res.get("success"):
                success_count += 1
            else:
                failed_count += 1
                if mode == STRICT:
                    self._emit(callbacks or {}, "on_log", "Modo STRICT: pipeline interrompido por falha.")
                    break

        final_status = "SUCCESS" if failed_count == 0 else ("FAILED" if success_count == 0 else "PARTIAL")
        db.finish_execution(self.execution_id, final_status)
        self._emit(callbacks or {}, "on_progress", 100)

        summary = f"Pipeline concluido. Sucesso: {success_count}, Falhas: {failed_count}, Total: {len(self.results)}."
        self._emit(callbacks or {}, "on_log", summary)
        return {
            "execution_id": self.execution_id,
            "status": final_status,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_tasks": len(self.results),
            "results": self.results,
            "summary": summary,
        }

    def execute_tasks(self, task_list: list[dict[str, Any]]) -> dict[str, Any]:
        selected_tasks = [task.get("id") for task in task_list if task.get("id")]
        context: dict[str, Any] = {}
        for task in task_list:
            context.update(task.get("params", {}))
        return self.run(selected_tasks=selected_tasks, context=context, mode=SAFE, callbacks={})
