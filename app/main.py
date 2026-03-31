import sys
import os
import argparse
import logging
from app.utils import admin, logger, file_utils
from app.database import db
from app.gui import App
from app.config import settings

def parse_args():
    parser = argparse.ArgumentParser(description="Windows Provisioning Assistant v2")
    parser.add_argument("--profile", type=str, help="Executar um perfil específico automaticamente")
    parser.add_argument("--silent", action="store_true", help="Executar em modo silencioso (sem interface)")
    return parser.parse_args()

def handle_silent_mode(args):
    """Executa o provisionamento em modo silencioso baseado em um perfil."""
    from app.modules.provisioning_pipeline import ProvisioningPipeline
    from app.modules.task_registry import get_available_tasks
    
    profiles = file_utils.load_json(settings.PROFILES_PATH)
    profile_name = args.profile
    
    if profile_name not in profiles:
        print(f"Erro: Perfil '{profile_name}' não encontrado.")
        sys.exit(1)
        
    profile_data = profiles[profile_name]
    tasks = [{"id": tid} for tid in profile_data.get("tasks", [])]
    
    print(f"Iniciando Provisionamento Silencioso: {profile_name}")
    pipeline = ProvisioningPipeline()
    results = pipeline.execute_tasks(tasks)
    
    print(f"Resultado Final: {results['status']}")
    sys.exit(0 if results['status'] == 'SUCCESS' else 1)

def main():
    args = parse_args()
    
    # 1. Configurar Logger
    log = logger.setup_logger()
    log.info("="*60)
    log.info(f"{settings.APP_NAME} v{settings.APP_VERSION} iniciando...")
    
    # 2. Verificar Admin
    is_admin = admin.is_admin()
    if not is_admin:
        log.warning("Sem privilégios de Administrador. Tentando elevar...")
        if admin.run_as_admin():
            # Se conseguiu elevar, o processo atual fecha e um novo abre
            sys.exit(0)
        else:
            log.error("Elevação bloqueada ou negada. Prosseguindo em modo limitado.")
    
    # 3. Inicializar Banco de Dados
    db.initialize_db()
    
    # 4. Modo Silencioso
    if args.silent and args.profile:
        handle_silent_mode(args)
        return

    # 5. Iniciar Interface Gráfica
    app = App(is_admin=is_admin)
    app.mainloop()

if __name__ == "__main__":
    main()
