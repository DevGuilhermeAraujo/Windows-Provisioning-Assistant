import logging
import os
from datetime import datetime

class GUILogHandler(logging.Handler):
    """Um handler de log personalizado que envia logs para a GUI."""
    def __init__(self, text_widget_callback):
        super().__init__()
        self.text_widget_callback = text_widget_callback

    def emit(self, record):
        log_entry = self.format(record)
        # Envia a mensagem formatada para a função da GUI
        if self.text_widget_callback:
            self.text_widget_callback(f"{log_entry}\n")

def setup_logger(log_file="logs/app.log", gui_callback=None):
    """Configura o logger principal e adiciona handlers."""
    # Criar diretório de logs se não existir
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("WindowsProvisioningAssistant")
    logger.setLevel(logging.DEBUG)

    # Limpa handlers existentes (se houver)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Handler do arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler do Console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para a GUI (se fornecido)
    if gui_callback:
        gui_handler = GUILogHandler(gui_callback)
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)

    return logger

def get_logger():
    """Retorna o logger configurado."""
    return logging.getLogger("WindowsProvisioningAssistant")
