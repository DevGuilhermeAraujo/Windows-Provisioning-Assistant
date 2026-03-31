"""
Pipeline de execução de tarefas de provisionamento.
Orquestra a execução de múltiplas tasks, registra no DB e reporta progresso.
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Callable

from app.modules.task_registry import get_task_function
from app.database import db
from app.utils import system_info

logger = logging.getLogger("WindowsProvisioningAssistant")

class ProvisioningPipeline:
    def __init__(self, execution_id: int = None):
        self.execution_id = execution_id
        self.results = []
        self.on_progress: Callable[[int, str], None] = None
        self.on_task_complete: Callable[[str, bool, str], None] = None

    def set_callbacks(self, on_progress=None, on_task_complete=None):
        self.on_progress = on_progress
        self.on_task_complete = on_task_complete

    def execute_tasks(self, task_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executa uma lista de tarefas sequencialmente.
        
        Args:
            task_list: Lista de dicionários {'id': id_da_task, 'args': [], 'kwargs': {}}
        """
        total_tasks = len(task_list)
        if total_tasks == 0:
            return {"status": "EMPTY", "results": []}

        logger.info(f"[Pipeline] Iniciando execução de {total_tasks} tarefas...")
        
        # Se não tiver execution_id, cria um novo no DB
        if not self.execution_id:
            username = system_info.get_full_system_info().get("username", "unknown")
            computer_name = system_info.get_current_hostname()
            self.execution_id = db.start_execution(username, computer_name)

        success_count = 0
        
        for i, task_info in enumerate(task_list):
            task_id = task_info.get("id")
            params = task_info.get("params", {})
            kwargs = task_info.get("kwargs", params) # Se kwargs não existir, usa params
            args = task_info.get("args", [])
            
            task_func = get_task_function(task_id)
            
            # Notifica progresso
            if self.on_progress:
                self.on_progress(int((i / total_tasks) * 100), f"Executando {task_id}...")

            if not task_func:
                error_msg = f"Task '{task_id}' não encontrada no registro."
                logger.error(f"[Pipeline] {error_msg}")
                res = {
                    "task_name": task_id,
                    "success": False,
                    "message": error_msg,
                    "errors": [error_msg]
                }
            else:
                start_time = time.time()
                try:
                    # Executa a função do serviço
                    res = task_func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"[Pipeline] Crash na task '{task_id}': {error_msg}")
                    res = {
                        "task_name": task_id,
                        "success": False,
                        "message": f"Erro inesperado: {error_msg}",
                        "errors": [error_msg]
                    }
                
                duration_ms = int((time.time() - start_time) * 1000)
                res["duration_ms"] = duration_ms

            # Registra no DB
            db.log_task(
                self.execution_id,
                res.get("task_name", task_id),
                res.get("success", False),
                res.get("message", ""),
                "; ".join(res.get("errors", [])),
                res.get("duration_ms", 0)
            )

            if res.get("success"):
                success_count += 1
            
            self.results.append(res)
            
            if self.on_task_complete:
                self.on_task_complete(task_id, res.get("success"), res.get("message"))

        # Finaliza execução no DB
        final_status = "SUCCESS" if success_count == total_tasks else "PARTIAL"
        if success_count == 0: 
            final_status = "FAILED"
            
        db.finish_execution(self.execution_id, final_status)
        
        if self.on_progress:
            self.on_progress(100, "Concluído.")

        logger.info(f"[Pipeline] Execução finalizada com status: {final_status}")
        
        return {
            "execution_id": self.execution_id,
            "status": final_status,
            "success_count": success_count,
            "total_tasks": total_tasks,
            "results": self.results
        }
