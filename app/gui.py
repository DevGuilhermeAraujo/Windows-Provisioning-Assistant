import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
import logging
import threading
import os
from datetime import datetime

# Imports internos
from app.config import settings
from app.utils import system_info, ip_scanner, admin, file_utils
from app.database import db
from app.reports import report_generator, report_templates
from app.modules.provisioning_pipeline import ProvisioningPipeline
from app.modules.task_registry import get_available_tasks

logger = logging.getLogger("WindowsProvisioningAssistant")

class App(ctk.CTk):
    def __init__(self, is_admin: bool = True):
        super().__init__()
        self.is_admin = is_admin
        self.setup_window()
        self.init_state()
        self.create_layout()
        self.select_frame("dashboard")

    def setup_window(self):
        """Configurações básicas da janela principal."""
        self.title(f"{settings.APP_NAME} v{settings.APP_VERSION}" + ("" if self.is_admin else " [LIMITADO]"))
        self.geometry(f"{settings.WINDOW_WIDTH}x{settings.WINDOW_HEIGHT}")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.set_appearance_mode(settings.APPEARANCE_MODE)
        ctk.set_default_color_theme(settings.COLOR_THEME)

    def init_state(self):
        """Inicializa variáveis de estado da aplicação."""
        self.current_frame = None
        self.execution_history = []
        self.selected_tasks = []
        self.profiles = file_utils.load_json(settings.PROFILES_PATH)
        self.software_state = {name: False for name in settings.WINGET_PACKAGES.keys()} 

    def create_layout(self):
        """Cria os componentes principais: Banner, Sidebar e Main Content."""
        # 1. Banner de Alerta (se não for admin)
        if not self.is_admin:
            self.warning_bar = ctk.CTkFrame(self, fg_color="#7d3c00", height=35, corner_radius=0)
            self.warning_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
            ctk.CTkLabel(self.warning_bar, text="⚠️ SEM PRIVILÉGIOS DE ADMIN. Algumas automações irão falhar.", 
                        text_color="#FFD700", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)

        # 2. Sidebar de Navegação
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.create_sidebar_content()

        # 3. Main Content Area
        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)

        # 4. Log Real-time (Bottom)
        self.log_area = ctk.CTkTextbox(self, height=150, font=("Consolas", 12), state="disabled")
        self.log_area.grid(row=2, column=1, sticky="ew", padx=20, pady=(0, 20))

    def create_sidebar_content(self):
        """Popula a barra lateral com botões de navegação."""
        ctk.CTkLabel(self.sidebar, text="WPA Business", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=30)
        
        self.nav_btns = {}
        menu = [
            ("dashboard", "🏠 Dashboard"),
            ("provisioning", "🚀 Provisionamento"),
            ("network", "🌐 Rede & Scanner"),
            ("domain", "🏢 Domínio AD"),
            ("software", "📦 Softwares"),
            ("security", "🛡️ Segurança"),
            ("reports", "📄 Relatórios"),
            ("history", "🕒 Histórico")
        ]
        
        for frame_id, label in menu:
            btn = ctk.CTkButton(self.sidebar, text=label, anchor="w", fg_color="transparent",
                               hover_color=settings.BG_CARD, command=lambda f=frame_id: self.select_frame(f))
            btn.pack(padx=15, pady=5, fill="x")
            self.nav_btns[frame_id] = btn

    def select_frame(self, name):
        """Alterna entre as abas da aplicação."""
        for btn in self.nav_btns.values():
            btn.configure(fg_color="transparent")
        self.nav_btns[name].configure(fg_color=settings.ACCENT_COLOR)
        
        # Limpa o frame atual
        if self.current_frame:
            self.current_frame.destroy()
            
        # Cria o novo frame
        if name == "dashboard":
            self.current_frame = DashboardFrame(self.main_content, self)
        elif name == "provisioning":
            self.current_frame = ProvisioningFrame(self.main_content, self)
        elif name == "network":
            self.current_frame = NetworkFrame(self.main_content, self)
        elif name == "domain":
            self.current_frame = DomainFrame(self.main_content, self)
        elif name == "software":
            self.current_frame = SoftwareFrame(self.main_content, self)
        elif name == "security":
            self.current_frame = SecurityFrame(self.main_content, self)
        elif name == "reports":
            self.current_frame = ReportFrame(self.main_content, self)
        elif name == "history":
            self.current_frame = HistoryFrame(self.main_content, self)
        
        if self.current_frame:
            self.current_frame.grid(row=0, column=0, sticky="nsew")

    def update_log(self, message: str):
        """Adiciona mensagem ao log da interface."""
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def get_frame(self, name):
        """Busca um frame específico se ele estiver ativo (não recomendado usar em produção, mas útil para o protótipo)."""
        # Como limpamos o frame no select_frame, só conseguiremos acessar o ATUAL.
        # Numa App real, os frames deveriam ser persistentes ou o estado ser centralizado no controller.
        # Para este caso, vamos garantir que State seja acessado.
        return self.current_frame if hasattr(self.current_frame, '__class__') and self.current_frame.__class__.__name__.lower().startswith(name) else None

# --- CLASSES DE FRAMES (ABAS) ---

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure((0, 1), weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Dashboard do Sistema", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        # Coleta infos em thread para não travar
        threading.Thread(target=self.load_info, daemon=True).start()

    def load_info(self):
        info = system_info.get_full_system_info()
        if self.winfo_exists():
            self.after(0, lambda: self.display_info(info))

    def display_info(self, info):
        # Cartão de Sistema
        card_sys = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        card_sys.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card_sys, text="Computador", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(card_sys, text=f"Host: {info['hostname']}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_sys, text=f"Serial: {info['serial']}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_sys, text=f"SO: {info['win_caption']}", text_color=settings.TEXT_MUTED).pack(pady=(0, 10))

        # Cartão de Hardware
        card_hw = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        card_hw.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card_hw, text="Hardware", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(card_hw, text=f"CPU: {info['cpu']}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_hw, text=f"RAM: {info['ram_gb']} GB", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_hw, text=f"Rede: {info['ip']}", text_color=settings.TEXT_MUTED).pack(pady=(0, 10))

class TaskItem(ctk.CTkFrame):
    """Componente para cada item da lista de provisionamento (Accordion)."""
    def __init__(self, parent, task_id, label, has_inputs=False):
        super().__init__(parent, fg_color="transparent")
        self.task_id = task_id
        self.has_inputs = has_inputs
        self.expanded = False
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        
        # Checkbox
        self.var = tk.BooleanVar(value=True)
        self.check = ctk.CTkCheckBox(self, text=label, variable=self.var, font=ctk.CTkFont(weight="bold"))
        self.check.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Botão de Expansão (Seta)
        if has_inputs:
            self.btn_expand = ctk.CTkButton(self, text="▼", width=30, fg_color="transparent", 
                                           hover_color=settings.BG_CARD, command=self.toggle)
            self.btn_expand.grid(row=0, column=2, padx=10, pady=10, sticky="e")
            
            # Frame de Inputs (Escondido por padrão)
            self.input_frame = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
            # Não damos grid ainda
            self.inputs = {} 
        else:
            ctk.CTkLabel(self, text="").grid(row=0, column=2, padx=10)

    def toggle(self):
        if not self.expanded:
            self.input_frame.grid(row=1, column=0, columnspan=3, padx=30, pady=(0, 10), sticky="ew")
            self.btn_expand.configure(text="▲")
        else:
            self.input_frame.grid_forget()
            self.btn_expand.configure(text="▼")
        self.expanded = not self.expanded

    def add_input(self, key, label, placeholder=""):
        row = len(self.inputs)
        ctk.CTkLabel(self.input_frame, text=label).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        entry = ctk.CTkEntry(self.input_frame, placeholder_text=placeholder, width=200)
        entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        self.inputs[key] = entry
        self.input_frame.grid_columnconfigure(1, weight=1)

    def get_params(self):
        return {k: v.get() for k, v in self.inputs.items()}

class ProvisioningFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Pipeline de Provisionamento", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Checklist de tarefas (Accordion)
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=1, column=0, sticky="nsew", pady=10)
        
        self.items = {}
        
        # 1. Hostname
        item_h = TaskItem(self.scroll, "hostname", "Alterar Hostname", has_inputs=True)
        item_h.add_input("new_name", "Novo Nome:", "Ex: PC-VENDAS-01")
        item_h.pack(fill="x", pady=2)
        self.items["hostname"] = item_h
        
        # 2. Rede
        item_net = TaskItem(self.scroll, "static_ip", "Configurar IP Fixo", has_inputs=True)
        item_net.add_input("ip", "Endereço IP:", "192.168.1.50")
        item_net.add_input("mask", "Máscara:", "255.255.255.0")
        item_net.add_input("gateway", "Gateway:", "192.168.1.1")
        item_net.pack(fill="x", pady=2)
        self.items["static_ip"] = item_net
        
        # Outras tasks simples
        simple_tasks = [
            ("time_sync", "Sincronizar NTP"),
            ("perf_plan", "Plano de Alta Performance"),
            ("firewall_on", "Ativar Firewall"),
            ("rdp_on", "Habilitar RDP"),
            ("install_apps", "Instalar Softwares"),
            ("cleanup", "Limpeza de Sistema")
        ]
        
        for tid, label in simple_tasks:
            item = TaskItem(self.scroll, tid, label)
            item.pack(fill="x", pady=2)
            self.items[tid] = item

        self.btn_run = ctk.CTkButton(self, text="🚀 Executar Provisionamento", height=45, fg_color=settings.ACCENT_COLOR, command=self.run_pipeline)
        self.btn_run.grid(row=2, column=0, pady=20)
        
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=3, column=0, sticky="ew", pady=10)
        self.progress.set(0)

    def run_pipeline(self):
        selected = []
        for tid, item in self.items.items():
            if item.var.get():
                params = item.get_params()
                
                # Regras especiais de parâmetros
                if tid == "static_ip":
                    # Detectar adaptador automaticamente
                    from app.services.network_service import run_powershell
                    res = run_powershell("Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -First 1 -ExpandProperty Name")
                    params["adapter_name"] = res["output"] if res["success"] else "Ethernet"
                
                elif tid == "install_apps":
                    # Pega exatamente o que foi marcado na aba lateral de Softwares
                    params["packages"] = [name for name, selected_sw in self.controller.software_state.items() if selected_sw]
                
                selected.append({"id": tid, "params": params})

        if not selected:
            messagebox.showwarning("Aviso", "Selecione ao menos uma tarefa.")
            return

        self.btn_run.configure(state="disabled")
        
        def run():
            pipe = ProvisioningPipeline()
            pipe.set_callbacks(
                on_progress=lambda p, m: self.update_safe(lambda: self.update_progress(p, m)),
                on_task_complete=lambda t, s, m: self.update_safe(lambda: self.controller.update_log(f"{t}: {'OK' if s else 'ERRO'} - {m}"))
            )
            pipe.execute_tasks(selected)
            self.update_safe(self.finalize_run)

        threading.Thread(target=run, daemon=True).start()

    def finalize_run(self):
        self.btn_run.configure(state="normal")
        messagebox.showinfo("Sucesso", "Provisionamento concluído!")

    def update_safe(self, func):
        """Executa uma função na thread principal apenas se o widget ainda existir."""
        if self.winfo_exists():
            self.after(0, func)

    def update_progress(self, val, msg):
        self.progress.set(val / 100)
        self.controller.update_log(msg)

class NetworkFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Rede & Scanner", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Scanner Controls
        scan_bar = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        scan_bar.grid(row=1, column=0, sticky="ew", pady=10)
        
        ctk.CTkLabel(scan_bar, text="Range CIDR:").pack(side="left", padx=10)
        self.entry_cidr = ctk.CTkEntry(scan_bar, placeholder_text="192.168.1.0/24")
        self.entry_cidr.pack(side="left", padx=10, fill="x", expand=True)
        
        self.btn_scan = ctk.CTkButton(scan_bar, text="🔍 Scanner de IPs", width=120, command=self.run_scanner)
        self.btn_scan.pack(side="left", padx=10)
        
        # Results Table (Simulated with Text)
        self.results_box = ctk.CTkTextbox(self, height=300)
        self.results_box.grid(row=2, column=0, sticky="nsew", pady=10)
        self.results_box.insert("end", "Inicie um scan para ver IPs livres/ocupados...")

    def run_scanner(self):
        cidr = self.entry_cidr.get()
        if not cidr:
            messagebox.showwarning("Aviso", "Informe um range CIDR (ex: 192.168.1.0/24)")
            return
            
        self.btn_scan.configure(state="disabled")
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", f"Iniciando scan em {cidr}...")
        
        def do_scan():
            res = ip_scanner.scan_network(cidr)
            if self.winfo_exists():
                self.after(0, lambda: self.show_results(res))
            
        threading.Thread(target=do_scan, daemon=True).start()

    def show_results(self, res):
        self.btn_scan.configure(state="normal")
        self.results_box.delete("1.0", "end")
        if "error" in res:
            self.results_box.insert("end", f"Erro: {res['error']}")
            return
            
        self.results_box.insert("end", f"Scan Completo em {res['network']}\n")
        self.results_box.insert("end", f"Ocupados: {len(res['occupied'])} | Livres: {len(res['free'])}\n\n")
        self.results_box.insert("end", "Sugestões de IPs Livres:\n")
        for ip in res['suggestions']:
            self.results_box.insert("end", f"  - {ip}\n")

class DomainFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Domínio Active Directory", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        form = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        form.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(form, text="Domínio:").pack(padx=20, pady=5, anchor="w")
        self.entry_domain = ctk.CTkEntry(form, width=300)
        self.entry_domain.pack(padx=20, pady=5, anchor="w")
        
        ctk.CTkLabel(form, text="Usuário Admin:").pack(padx=20, pady=5, anchor="w")
        self.entry_user = ctk.CTkEntry(form, width=300)
        self.entry_user.pack(padx=20, pady=5, anchor="w")
        
        ctk.CTkLabel(form, text="Senha:").pack(padx=20, pady=5, anchor="w")
        self.entry_pass = ctk.CTkEntry(form, width=300, show="*")
        self.entry_pass.pack(padx=20, pady=5, anchor="w")
        
        self.btn_join = ctk.CTkButton(form, text="🏢 Ingressar no Domínio", command=self.join_domain)
        self.btn_join.pack(padx=20, pady=30, anchor="w")

    def join_domain(self):
        domain = self.entry_domain.get()
        user = self.entry_user.get()
        password = self.entry_pass.get()
        
        if not domain or not user or not password:
            messagebox.showwarning("Aviso", "Preencha todos os campos do domínio.")
            return

        from app.services.domain_service import join_domain
        self.controller.update_log(f"Iniciando tentativa de ingressar em {domain}...")
        
        def run():
            res = join_domain(domain, user, password)
            if self.winfo_exists():
                self.after(0, lambda: messagebox.showinfo("Resultado", res["message"]))
            
        threading.Thread(target=run, daemon=True).start()

class SoftwareFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Instalação de Softwares", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        self.scroll = ctk.CTkScrollableFrame(self, height=400)
        self.scroll.grid(row=1, column=0, sticky="nsew", pady=10)
        
        self.sw_vars = {}
        for name in settings.WINGET_PACKAGES.keys():
            # Carregar estado persistente do controller
            initial_val = self.controller.software_state.get(name, False)
            var = tk.BooleanVar(value=initial_val)
            
            cb = ctk.CTkCheckBox(self.scroll, text=name, variable=var, 
                                 command=lambda n=name, v=var: self.save_state(n, v))
            cb.pack(anchor="w", padx=20, pady=5)
            self.sw_vars[name] = var

        self.btn_install = ctk.CTkButton(self, text="📦 Instalar Selecionados", command=self.install_sw)
        self.btn_install.grid(row=2, column=0, pady=20)

    def save_state(self, name, var):
        """Salva o estado no controller para não perder ao trocar de aba."""
        self.controller.software_state[name] = var.get()

    def install_sw(self):
        to_install = [name for name, var in self.sw_vars.items() if var.get()]
        if not to_install:
            messagebox.showwarning("Aviso", "Selecione ao menos um software.")
            return
            
        self.btn_install.configure(state="disabled")
        from app.services.software_installer import install_multiple
        
        def run():
            res = install_multiple(to_install)
            if self.winfo_exists():
                self.after(0, lambda: self.btn_install.configure(state="normal"))
                self.after(0, lambda: messagebox.showinfo("Resultado", res["message"]))
            
        threading.Thread(target=run, daemon=True).start()

class SecurityFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Segurança & Usuários", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Firewall
        fw_box = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        fw_box.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(fw_box, text="Firewall do Windows", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=20)
        ctk.CTkButton(fw_box, text="Ativar Firewall", width=120, command=lambda: self.run_task("firewall_on")).pack(side="right", padx=10)
        
        # RDP
        rdp_box = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        rdp_box.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(rdp_box, text="Acesso Remoto (RDP)", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=20)
        ctk.CTkButton(rdp_box, text="Habilitar RDP", width=120, command=lambda: self.run_task("rdp_on")).pack(side="right", padx=10)

        # BitLocker
        bl_box = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        bl_box.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(bl_box, text="BitLocker (C:)", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=20)
        ctk.CTkButton(bl_box, text="Criptografar", width=120, command=lambda: self.run_task("bitlocker")).pack(side="right", padx=10)

    def run_task(self, task_id):
        from app.modules.task_registry import get_task_function
        func = get_task_function(task_id)
        if func:
            def run():
                res = func()
                if self.winfo_exists():
                    self.after(0, lambda: messagebox.showinfo("Task", res["message"]))
            threading.Thread(target=run, daemon=True).start()

class ReportFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Relatórios & Exportações", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        btn_box = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        btn_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkButton(btn_box, text="📂 Abrir Pasta de Relatórios", command=lambda: file_utils.open_folder(settings.REPORTS_DIR)).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(btn_box, text="📊 Exportar Histórico para CSV", command=self.export_csv).pack(pady=10, padx=20, fill="x")

    def export_csv(self):
        res = report_generator.export_db_history_to_csv()
        if res["success"]:
            messagebox.showinfo("Sucesso", f"Histórico exportado:\n{res['filepath']}")
        else:
            messagebox.showerror("Erro", res["message"])

class HistoryFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Histórico de Execuções", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        self.scroll = ctk.CTkScrollableFrame(self, height=500)
        self.scroll.grid(row=1, column=0, sticky="nsew", pady=10)
        self.load_history()

    def load_history(self):
        data = db.get_all_executions()
        for i, run in enumerate(data):
            f = ctk.CTkFrame(self.scroll, fg_color=settings.BG_CARD)
            f.pack(fill="x", pady=5, padx=10)
            
            status_color = settings.SUCCESS_COLOR if run['status'] == 'SUCCESS' else settings.ERROR_COLOR
            ctk.CTkLabel(f, text=f"ID: {run['id']} | {run['datetime_start'][:19]} | {run['computer_name']}", font=ctk.CTkFont(size=12)).pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(f, text=run['status'], text_color=status_color, font=ctk.CTkFont(weight="bold")).pack(side="right", padx=15)
