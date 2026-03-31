"""
Entry point para o Windows Provisioning Assistant.
Execute a partir da raiz do projeto: python run.py
"""
import sys
import os

# Adiciona o diretório atual ao sys.path para garantir que o pacote 'app' seja encontrado
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import main
except ImportError as e:
    print(f"Erro ao carregar o aplicativo: {e}")
    sys.exit(1)

if __name__ == "__main__":
    main()
