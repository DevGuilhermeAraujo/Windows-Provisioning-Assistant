# 🖥️ Windows Provisioning Assistant

Uma ferramenta com interface gráfica moderna para automatizar a configuração inicial de computadores Windows em ambientes corporativos.

---

## 📋 Descrição

O **Windows Provisioning Assistant** foi desenvolvido para auxiliar técnicos e analistas de TI a configurar rapidamente um computador Windows sem precisar acessar manualmente diversas telas do sistema operacional. Com uma interface intuitiva e moderna, a ferramenta centraliza as principais tarefas de provisionamento em um único lugar.

---

## 🎯 Objetivo

Automatizar e documentar o processo de provisionamento de workstations Windows em ambientes corporativos, reduzindo erros humanos e o tempo de configuração inicial.

---

## ✅ Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 🖥️ **Renomear Computador** | Altera o hostname da máquina via PowerShell |
| 🌐 **Configuração de Rede** | Define DHCP ou IP estático, máscara, gateway e DNS |
| 🔒 **Ingresso no Domínio AD** | Adiciona a máquina a um domínio Active Directory |
| 👤 **Usuário Local Admin** | Cria um usuário local e o adiciona ao grupo Administradores |
| 📊 **Logs em Tempo Real** | Exibe e registra todas as ações em arquivo de log |
| 📄 **Relatório JSON** | Gera um relatório completo da execução em formato JSON |

---

## 🗂️ Estrutura do Projeto

```
windows-provisioning-assistant/
├── app/
│   ├── main.py              # Ponto de entrada da aplicação
│   ├── gui.py               # Interface gráfica (CustomTkinter)
│   ├── utils/
│   │   ├── admin.py         # Verificação de privilégios
│   │   ├── logger.py        # Configuração de logs
│   │   ├── validators.py    # Validações (IP, hostname, etc.)
│   │   ├── system_info.py   # Informações do sistema
│   │   └── command_runner.py # Execução de comandos PowerShell
│   ├── services/
│   │   ├── hostname_service.py  # Renomear computador
│   │   ├── network_service.py   # Configuração de rede
│   │   ├── domain_service.py    # Ingresso no domínio AD
│   │   └── user_service.py      # Criação de usuário local
│   ├── reports/
│   │   └── report_generator.py  # Geração de relatório JSON
│   └── config/
│       └── settings.py          # Configurações globais
├── logs/                    # Logs gerados automaticamente
├── output/
│   ├── reports/             # Relatórios JSON
│   └── exports/             # Exportações futuras
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Requisitos

- **Python 3.11+**
- **Windows 10 / 11** (ou Windows Server 2016+)
- **⚠️ DEVE ser executado como Administrador**
- PowerShell disponível no sistema (padrão em Windows)

---

## 📦 Instalação de Dependências

```bash
pip install -r requirements.txt
```

---

## 🚀 Como Executar

> **IMPORTANTE:** A ferramenta precisa de privilégios de Administrador para funcionar.

**Opção 1 – Executar diretamente (com elevação automática):**
```bash
python app/main.py
```
> O programa detectará se não está rodando como Admin e pedirá elevação automaticamente.

**Opção 2 – Abrir terminal como Administrador manualmente:**
1. Clique com o botão direito no **Prompt de Comando** ou **PowerShell**
2. Selecione **"Executar como administrador"**
3. Navegue até a pasta do projeto:
   ```
   cd caminho\para\windows-provisioning-assistant
   ```
4. Execute:
   ```bash
   python app/main.py
   ```

---

## 📊 Relatórios

Os relatórios são gerados em formato JSON em:
```
output/reports/report_YYYY-MM-DD_HH-MM.json
```

Exemplo de conteúdo:
```json
{
    "report_info": {
        "generated_at": "2026-03-31T09:00:00",
        "version": "1.0.0"
    },
    "execution_summary": {
        "hostname_atual": "DESKTOP-XXXXX",
        "logs_execucao": ["..."]
    }
}
```

---

## 📁 Logs

Os logs de execução são armazenados automaticamente em:
```
logs/app.log
```

---

## 🛡️ Boas Práticas Implementadas

- ✅ Verificação e elevação automática de privilégios de Administrador
- ✅ Tratamento de erros em todo o código (`try/except`)
- ✅ Validação de entradas antes de executar qualquer comando
- ✅ Logs completos de todas as ações realizadas
- ✅ Operações executadas em threads para não travar a interface
- ✅ Comandos PowerShell isolados por módulo de serviço
- ✅ Relatório JSON gerado ao final da sessão

---

## 👨‍💻 Developed by

[DevGuilhermeAraujo](https://github.com/DevGuilhermeAraujo)

---

> ⚠️ **Aviso:** Esta ferramenta executa operações críticas no sistema operacional. Use com responsabilidade em ambientes de produção.
