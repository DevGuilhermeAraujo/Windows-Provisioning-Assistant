# 🚀 Windows Provisioning Assistant (WPA Business)

![Versão](https://img.shields.io/badge/versão-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![OS](https://img.shields.io/badge/os-windows-0078d6)

O **Windows Provisioning Assistant v2** é uma ferramenta de nível corporativo projetada para automatizar o processo de padronização e preparação de novas máquinas em ambientes de TI.

## 🎯 Objetivo
Transformar o provisionamento manual de 40 minutos em um clique de 5 minutos, garantindo que todas as máquinas sigam exatamente as mesmas políticas e configurações da empresa.

## ✨ Principais Funcionalidades (v2)
- **Checklist Pipeline**: Selecione as tarefas e execute em massa com barra de progresso real.
- **8 Abas de Gestão**: Dashboard, Provisionamento, Rede, Domínio, Software, Segurança, Relatórios e Histórico.
- **Scanner de Rede**: Detecta IPs livres e ocupados na sua subrede para sugerir o melhor IP fixo.
- **Automação via winget**: Instale navegadores e utilitários silenciosamente.
- **Integração com Domínio**: Ingressar em domínio AD com validação prévia.
- **Histórico SQLite**: Todas as execuções são salvas em um banco de dados local.
- **Relatórios Automatizados**: Gera relatórios JSON e exporta auditoria para CSV.
- **Perfis Corporativos**: Carregue predefinições para "Escritório", "PDV", "Servidor" ou "Notebook".

## 🛠️ Tecnologias
- **Python 3.11+**
- **CustomTkinter** (Interface Moderna)
- **PowerShell** (Core de Automação)
- **SQLite3** (Banco de Dados)
- **Fernet/Cryptography** (Proteção de dados locais)

## 📂 Estrutura Modular
- `app/services`: 14 módulos de automação (BitLocker, Firewall, NTP, PowerPlan, Cleanup, etc).
- `app/modules`: Orquestrador de pipeline e registro de tarefas.
- `app/database`: Gestão de histórico de execuções.
- `app/utils`: Scanners, validadores e utilitários de sistema.

## 🚀 Como Executar
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute a aplicação (modo Admin recomendado):
   ```bash
   python run.py
   ```

## 📦 Como Gerar o Executável
Use o PyInstaller com o arquivo de especificação fornecido:
```bash
pyinstaller --noconfirm build.spec
```
O executável será gerado na pasta `dist/WindowsProvisioningAssistant`.


## 👨‍💻 Autor

Desenvolvido por Guilherme Araujo
📌 Desenvolvedor / TI
🔗 LinkedIn: (https://www.linkedin.com/in/guilherme-araujo-b2b6a8164/)