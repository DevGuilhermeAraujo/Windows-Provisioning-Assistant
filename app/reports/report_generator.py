import json
import csv
import os
import logging
from datetime import datetime
from app.utils import system_info, file_utils
from app.config import settings

logger = logging.getLogger("WindowsProvisioningAssistant")

def generate_full_report(pipeline_results: dict, output_format: str = "json"):
    """
    Gera um relatório completo de uma execução de provisionamento.
    
    Args:
        pipeline_results: Dicionário retornado por ProvisioningPipeline.execute_tasks
        output_format: "json" ou "csv"
    """
    logger.info(f"[Report] Gerando relatório no formato {output_format}...")
    
    # 1. Coletar estado atual do sistema para o cabeçalho
    sys_info = system_info.get_full_system_info()
    
    report_data = {
        "metadata": {
            "version": settings.APP_VERSION,
            "generated_at": datetime.now().isoformat(),
            "execution_id": pipeline_results.get("execution_id")
        },
        "system_info": sys_info,
        "execution_summary": {
            "status": pipeline_results.get("status"),
            "success_count": pipeline_results.get("success_count"),
            "total_tasks": pipeline_results.get("total_tasks"),
            "results": pipeline_results.get("results", [])
        }
    }
    
    if output_format.lower() == "json":
        filepath = file_utils.timestamped_filename("report", "json", settings.REPORTS_DIR)
        success = file_utils.save_json(filepath, report_data)
        if success:
            logger.info(f"[Report] Relatório JSON gerado: {filepath}")
            return {"success": True, "filepath": filepath}
            
    elif output_format.lower() == "csv":
        filepath = file_utils.timestamped_filename("report", "csv", settings.EXPORTS_DIR)
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Cabeçalho
                writer.writerow(["Task Name", "Success", "Message", "Duration (ms)", "Errors"])
                # Dados
                for res in pipeline_results.get("results", []):
                    writer.writerow([
                        res.get("task_name"),
                        res.get("success"),
                        res.get("message"),
                        res.get("duration_ms"),
                        "; ".join(res.get("errors", []))
                    ])
            logger.info(f"[Report] Relatório CSV gerado: {filepath}")
            return {"success": True, "filepath": filepath}
        except Exception as e:
            logger.error(f"[Report] Erro ao gerar CSV: {e}")
            return {"success": False, "message": str(e)}

    return {"success": False, "message": "Formato inválido."}

def export_db_history_to_csv():
    """Exporta todo o histórico do SQLite para um arquivo CSV para auditoria."""
    from app.database import db
    executions = db.get_all_executions()
    
    filepath = file_utils.timestamped_filename("history_audit", "csv", settings.EXPORTS_DIR)
    
    try:
        if not executions:
            return {"success": False, "message": "Nenhum histórico encontrado."}
            
        keys = executions[0].keys()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(executions)
            
        logger.info(f"[Report] Auditoria de histórico exportada: {filepath}")
        return {"success": True, "filepath": filepath}
    except Exception as e:
        logger.error(f"[Report] Erro ao exportar histórico: {e}")
        return {"success": False, "message": str(e)}
