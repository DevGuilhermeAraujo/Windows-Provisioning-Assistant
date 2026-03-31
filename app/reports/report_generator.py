import json
import os
import logging
from datetime import datetime

def generate_report(data: dict, output_dir: str = "output/reports"):
    """Gera um relatório final em formato JSON."""
    logger = logging.getLogger("WindowsProvisioningAssistant")
    
    # 1. Criar diretório se não existir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 2. Nome do arquivo: report_YYYY-MM-DD_HH-MM.json
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"report_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # 3. Adicionar metadados
    report_content = {
        "report_info": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0.0"
        },
        "execution_summary": data
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_content, f, indent=4, ensure_ascii=False)
        
        msg = f"Relatório final gerado em: {filepath}"
        logger.info(msg)
        return {"success": True, "filepath": filepath}
    except Exception as e:
        msg = f"Erro ao gerar relatório JSON: {e}"
        logger.error(msg)
        return {"success": False, "message": msg}
