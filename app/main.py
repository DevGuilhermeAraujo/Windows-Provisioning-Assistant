"""
Windows Provisioning Assistant - Ponto de entrada principal.

Este arquivo verifica os privilégios de administrador, inicializa o logger
e abre a interface gráfica.
"""

import sys
import os

# Adiciona o diretório raiz do projeto ao path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.admin import is_admin, run_as_admin
from app.utils.logger import setup_logger
import customtkinter as ctk


def main():
    """Função principal de inicialização."""

    # 1. Verificar privilégios de administrador
    if not is_admin():
        print("[AVISO] Não está rodando como Administrador. Tentando elevar privilégios...")
        run_as_admin()
        # Se chegou aqui, já pediu elevação e precisa encerrar o processo atual
        sys.exit(0)

    # 2. Inicializar o Logger (sem callback de GUI ainda - a GUI inicializará o seu próprio)
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info(f"Windows Provisioning Assistant iniciando...")
    logger.info(f"Usuário: {os.getenv('USERNAME', 'desconhecido')}")
    logger.info(f"Executando como Administrador: {is_admin()}")
    logger.info("=" * 60)

    # 3. Configurar tema e iniciar interface gráfica
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Import aqui para garantir que o logger já foi configurado
    from app.gui import App

    app = App()
    logger.info("Interface gráfica aberta com sucesso.")
    app.mainloop()
    logger.info("Aplicação encerrada pelo usuário.")


if __name__ == "__main__":
    main()
