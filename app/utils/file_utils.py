"""Utilitários de arquivos, diretórios e JSON."""

import os
import json
import shutil
import logging
from datetime import datetime

logger = logging.getLogger("WindowsProvisioningAssistant")


def ensure_directories(*paths: str):
    """Cria os diretórios especificados se não existirem."""
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)
            logger.debug(f"[FileUtils] Diretório criado: {path}")


def load_json(filepath: str, default=None):
    """Lê e retorna o conteúdo de um arquivo JSON. Retorna default em caso de erro."""
    if default is None:
        default = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"[FileUtils] Arquivo não encontrado: {filepath}")
        return default
    except json.JSONDecodeError as e:
        logger.error(f"[FileUtils] JSON inválido em {filepath}: {e}")
        return default


def save_json(filepath: str, data: dict, indent: int = 4) -> bool:
    """Salva um dicionário como JSON. Retorna True se sucesso."""
    try:
        ensure_directories(os.path.dirname(filepath))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"[FileUtils] Erro ao salvar JSON em {filepath}: {e}")
        return False


def timestamped_filename(prefix: str, extension: str, directory: str) -> str:
    """Gera um caminho de arquivo com timestamp. Ex: output/reports/report_2026-03-31_10-00-00.json"""
    ensure_directories(directory)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{prefix}_{timestamp}.{extension}"
    return os.path.join(directory, filename)


def open_folder(path: str):
    """Abre uma pasta no Explorer do Windows."""
    try:
        ensure_directories(path)
        os.startfile(os.path.abspath(path))
    except Exception as e:
        logger.error(f"[FileUtils] Não foi possível abrir a pasta {path}: {e}")


def backup_file(source_path: str, backup_dir: str) -> str:
    """Cria uma cópia de segurança de um arquivo. Retorna o caminho do backup."""
    try:
        ensure_directories(backup_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.basename(source_path)
        dest = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
        shutil.copy2(source_path, dest)
        return dest
    except Exception as e:
        logger.error(f"[FileUtils] Erro ao criar backup de {source_path}: {e}")
        return ""
