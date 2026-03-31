"""
Modelos e templates para relatórios profissionais.
"""

def get_summary_text(pipeline_results: dict) -> str:
    """Retorna um texto resumido do status da execução para exibição na UI."""
    status = pipeline_results.get("status", "UNKNOWN")
    success = pipeline_results.get("success_count", 0)
    total = pipeline_results.get("total_tasks", 0)
    
    if status == "SUCCESS":
        return f"🎉 Sucesso total! {success}/{total} tarefas concluídas sem erros."
    elif status == "PARTIAL":
        return f"⚠️ Sucesso parcial. {success}/{total} tarefas concluídas com êxito."
    else:
        return f"❌ Falha generalizada. Nenhuma das {total} tarefas foi completada com sucesso."

def format_task_details(task_result: dict) -> str:
    """Formata os detalhes de uma tarefa para visualização rápida no log ou relatório."""
    name = task_result.get("task_name", "Unknown")
    success = "✅" if task_result.get("success") else "❌"
    message = task_result.get("message", "")
    duration = task_result.get("duration_ms", 0)
    
    return f"{success} {name} ({duration}ms): {message}"
