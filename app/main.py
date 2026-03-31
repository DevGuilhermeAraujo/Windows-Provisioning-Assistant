"""
Windows Provisioning Assistant - Ponto de entrada principal.

Verifica privilégios de administrador, inicializa o logger e abre a GUI.
Se a elevação for bloqueada, o app ainda abre com avisos nas ações que precisam de admin.
"""

import sys
import os

# Adiciona o diretório raiz ao path para imports absolutos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.admin import is_admin, run_as_admin
from app.utils.logger import setup_logger


def main():
    """Função principal de inicialização."""

    # 1. Tentar elevar privilégios se necessário
    admin = is_admin()

    if not admin:
        print("[AVISO] Sem privilégios de Administrador. Tentando elevar...")
        elevated = run_as_admin()

        if elevated:
            # Elevação solicitada com sucesso — encerra o processo atual
            # O novo processo elevado continuará a execução
            sys.exit(0)
        else:
            # Elevação bloqueada (GPO, UAC restritivo, etc.)
            # Continua a execução em modo limitado com aviso na interface
            print("[AVISO] Elevação bloqueada ou negada. Abrindo em modo limitado.")

    # 2. Inicializar Logger
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info("Windows Provisioning Assistant iniciando...")
    logger.info(f"Usuário: {os.getenv('USERNAME', 'desconhecido')}")
    logger.info(f"Executando como Administrador: {admin}")
    if not admin:
        logger.warning(
            "MODO LIMITADO: sem privilégios de admin. "
            "Ações que exigem admin irão falhar com mensagem de erro."
        )
    logger.info("=" * 60)

    # 3. Configurar CustomTkinter e abrir GUI
    import customtkinter as ctk
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    from app.gui import App
    app = App(is_admin=admin)
    logger.info("Interface gráfica aberta com sucesso.")
    app.mainloop()
    logger.info("Aplicação encerrada pelo usuário.")


if __name__ == "__main__":
    main()
