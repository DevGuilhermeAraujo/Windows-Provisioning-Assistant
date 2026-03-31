"""
Banco de dados SQLite para histórico de execuções.
Gerencia conexão, criação de tabelas e operações CRUD.
"""

import sqlite3
import os
import logging
from datetime import datetime
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger("WindowsProvisioningAssistant")


def get_db_path() -> str:
    """Retorna o caminho absoluto do banco de dados."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, settings.DB_PATH)


@contextmanager
def get_connection():
    """Context manager para conexão segura com o banco."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"[DB] Erro na transação: {e}")
        raise
    finally:
        conn.close()


def initialize_db():
    """Cria as tabelas se não existirem."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS executions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime_start  TEXT NOT NULL,
                datetime_end    TEXT,
                username        TEXT,
                computer_name   TEXT,
                profile_used    TEXT,
                status          TEXT DEFAULT 'RUNNING',
                notes           TEXT
            );

            CREATE TABLE IF NOT EXISTS execution_tasks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id    INTEGER NOT NULL,
                task_name       TEXT NOT NULL,
                success         INTEGER NOT NULL DEFAULT 0,
                message         TEXT,
                error_details   TEXT,
                duration_ms     INTEGER,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (execution_id) REFERENCES executions(id)
            );
        """)
    logger.info("[DB] Banco de dados inicializado com sucesso.")


def start_execution(username: str, computer_name: str, profile: str = None) -> int:
    """Registra o início de uma nova execução. Retorna o ID da execução."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO executions (datetime_start, username, computer_name, profile_used, status)
               VALUES (?, ?, ?, ?, 'RUNNING')""",
            (datetime.now().isoformat(), username, computer_name, profile)
        )
        return cur.lastrowid


def finish_execution(execution_id: int, status: str = "SUCCESS"):
    """Atualiza o status final de uma execução."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE executions SET datetime_end=?, status=? WHERE id=?",
            (datetime.now().isoformat(), status, execution_id)
        )


def log_task(execution_id: int, task_name: str, success: bool,
             message: str = "", error: str = "", duration_ms: int = 0):
    """Registra o resultado de uma tarefa individual."""
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO execution_tasks
               (execution_id, task_name, success, message, error_details, duration_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (execution_id, task_name, int(success), message, error,
             duration_ms, datetime.now().isoformat())
        )


def get_all_executions() -> list:
    """Retorna todas as execuções em ordem decrescente de data."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM executions ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_execution_tasks(execution_id: int) -> list:
    """Retorna todas as tarefas de uma execução específica."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM execution_tasks WHERE execution_id=? ORDER BY id",
            (execution_id,)
        ).fetchall()
        return [dict(r) for r in rows]
