import json
import os
import logging

logger = logging.getLogger(__name__)

def load_json(path, default=None):
    """Carrega dados de um arquivo JSON."""
    if not os.path.exists(path):
        logger.warning(f"Arquivo não encontrado: {path}")
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON em {path}: {e}")
        return default
    except Exception as e:
        logger.error(f"Erro inesperado ao ler {path}: {e}")
        return default

def validate_profiles_data(data):
    """Valida se os dados de perfis estão no formato esperado."""
    if not isinstance(data, list):
        return False, "Data must be a list"
    for profile in data:
        if not isinstance(profile, dict):
            return False, "Each profile must be a dictionary"
        if "name" not in profile:
            return False, "Each profile must have a 'name' field"
    return True, ""

def save_json(path, data):
    """Salva dados em um arquivo JSON."""
    try:
        # Garante que o diretório exista
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar JSON em {path}: {e}")
        return False
