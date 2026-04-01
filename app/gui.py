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
from app.modules.context_builder import build_context

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
        self.profile_load_error = ""
        loaded_profiles = file_utils.load_json(settings.PROFILES_PATH, default=[])
        ok, err = file_utils.validate_profiles_data(loaded_profiles)
        if not ok:
            self.profiles = []
            self.profile_load_error = f"Perfis invalidos: {err}"
        else:
            self.profiles = loaded_profiles
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
        if self.profile_load_error:
            self.after(150, lambda: messagebox.showwarning("Profiles", f"Falha ao carregar profiles.json.\n{self.profile_load_error}"))

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
        from app.services import inventory_service
        # Mostra loading enquanto consulta (pode demorar no PowerShell)
        if self.winfo_exists():
            self.after(0, lambda: self.controller.update_log("Coletando inventario corporativo... aguarde."))
            
        info = inventory_service.get_full_inventory()
        if self.winfo_exists():
            self.after(0, lambda: self.display_info(info))

    def display_info(self, info):
        # Cartão de Sistema
        card_sys = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        card_sys.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card_sys, text="Computador", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(card_sys, text=f"Host: {info.get('hostname', 'N/A')}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_sys, text=f"Serial: {info.get('serial_number', 'N/A')}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_sys, text=f"Modelo: {info.get('model', 'N/A')}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_sys, text=f"SO: {info.get('os_version', 'N/A')}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_sys, text=f"Dominio: {info.get('domain_status', 'N/A')}", text_color=settings.TEXT_MUTED).pack(pady=(0, 10))

        # Cartão de Rede/Hardware
        card_hw = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        card_hw.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card_hw, text="Rede & Hardware", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        net = info.get("network", {})
        ctk.CTkLabel(card_hw, text=f"IP: {net.get('ip', 'N/A')}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_hw, text=f"Gateway: {net.get('gateway', 'N/A')}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_hw, text=f"DNS: {net.get('dns', 'N/A')}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_hw, text=f"CPU: {info.get('cpu', 'N/A')}", text_color=settings.TEXT_MUTED).pack()
        ctk.CTkLabel(card_hw, text=f"RAM: {info.get('ram', 'N/A')}", text_color=settings.TEXT_MUTED).pack(pady=(0, 10))

class Toast(ctk.CTkToplevel):
    """Notificação temporária estilo Toast Premium com transparência e animação."""
    def __init__(self, message, type="info", duration=3500):
        super().__init__()
        self.overrideredirect(True)
        self.attributes("-alpha", 0.0)  # Inicia invisível para animação
        self.attributes("-topmost", True)
        
        # Truque de transparência para Windows
        self.config(background="#010101")
        self.attributes("-transparentcolor", "#010101")
        
        # Cores e Ícones
        icons = {"success": "✅", "error": "❌", "info": "ℹ️", "warning": "⚠️"}
        bg_color = settings.SUCCESS_COLOR if type == "success" else settings.ERROR_COLOR if type == "error" else settings.INFO_COLOR
        icon = icons.get(type, "ℹ️")

        # Container Arredondado
        self.frame = ctk.CTkFrame(self, corner_radius=20, fg_color=bg_color, border_width=1, border_color="#ffffff")
        self.frame.pack(padx=10, pady=10)
        
        # Conteúdo
        content = ctk.CTkFrame(self.frame, fg_color="transparent")
        content.pack(padx=15, pady=8)
        
        ctk.CTkLabel(content, text=icon, font=ctk.CTkFont(size=18)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(content, text=message, font=ctk.CTkFont(size=13, weight="bold"), 
                    text_color="white").pack(side="left")
        
        # Posicionamento Dinâmico (Canto inferior direito)
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.winfo_screenwidth() - w - 40
        y = self.winfo_screenheight() - h - 80
        self.geometry(f"+{x}+{y}")
        
        # Animação de Fade-In
        self.fade_in()
        
        # Auto-destruição com Fade-Out
        self.after(duration, self.fade_out)

    def fade_in(self):
        curr_alpha = self.attributes("-alpha")
        if curr_alpha < 0.95:
            self.attributes("-alpha", curr_alpha + 0.1)
            self.after(20, self.fade_in)

    def fade_out(self):
        curr_alpha = self.attributes("-alpha")
        if curr_alpha > 0:
            self.attributes("-alpha", curr_alpha - 0.1)
            self.after(20, self.fade_out)
        else:
            self.destroy()

class TaskItem(ctk.CTkFrame):
    """Componente para cada item da lista de provisionamento (Accordion)."""
    def __init__(self, parent, task_id, label, has_inputs=False):
        super().__init__(parent, fg_color="transparent")
        self.task_id = task_id
        self.has_inputs = has_inputs
        self.expanded = False
        self.inputs = {} # Inicializa sempre para evitar AttributeError
        
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

    def add_select(self, key, label, options):
        row = len(self.inputs)
        ctk.CTkLabel(self.input_frame, text=label).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        combo = ctk.CTkComboBox(self.input_frame, values=options, width=200)
        combo.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        self.inputs[key] = combo
        self.input_frame.grid_columnconfigure(1, weight=1)

    def get_params(self):
        return {k: v.get() for k, v in self.inputs.items()}

class ProvisioningFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Busca adaptadores de rede reais antes de criar os widgets
        self.network_adapters = self.get_adapters()
        self.create_widgets()

    def get_adapters(self):
        """Busca nomes reais dos adaptadores de rede via PowerShell."""
        from app.utils.command_runner import run_powershell
        res = run_powershell("Get-NetAdapter | Select-Object -ExpandProperty Name")
        if res["success"] and res["output"]:
            return [line.strip() for line in res["output"].split("\n") if line.strip()]
        return ["Ethernet", "Wi-Fi"] # Fallback

    def create_widgets(self):
        ctk.CTkLabel(self, text="Pipeline de Provisionamento", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.grid(row=0, column=0, sticky="e")
        self.mode_var = tk.StringVar(value="SAFE")
        ctk.CTkLabel(mode_frame, text="Modo:").pack(side="left", padx=(0, 8))
        ctk.CTkRadioButton(mode_frame, text="SAFE", variable=self.mode_var, value="SAFE").pack(side="left", padx=4)
        ctk.CTkRadioButton(mode_frame, text="STRICT", variable=self.mode_var, value="STRICT").pack(side="left", padx=4)

        profile_bar = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        profile_bar.grid(row=1, column=0, sticky="ew", pady=(10, 5))
        ctk.CTkLabel(profile_bar, text="Profile:").pack(side="left", padx=(10, 8), pady=8)
        self.profile_values = [p.get("name", "") for p in self.controller.profiles]
        if not self.profile_values:
            self.profile_values = ["(sem perfis)"]
        self.profile_var = tk.StringVar(value=self.profile_values[0])
        self.profile_combo = ctk.CTkComboBox(
            profile_bar,
            values=self.profile_values,
            variable=self.profile_var,
            width=200,
            command=lambda _: self.apply_selected_profile(),
        )
        self.profile_combo.pack(side="left", padx=5, pady=8)
        ctk.CTkButton(profile_bar, text="Salvar Profile", width=110, command=self.open_save_profile_modal).pack(side="left", padx=5)
        ctk.CTkButton(profile_bar, text="Editar Profile", width=110, command=self.open_edit_profile_modal).pack(side="left", padx=5)
        
        # Checklist de tarefas (Accordion)
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=2, column=0, sticky="nsew", pady=10)
        
        self.items = {}
        
        # 1. Hostname
        item_h = TaskItem(self.scroll, "hostname", "Alterar Hostname", has_inputs=True)
        item_h.add_input("new_hostname", "Novo Nome:", "Ex: PC-VENDAS-01")
        item_h.pack(fill="x", pady=2)
        self.items["hostname"] = item_h
        
        # 2. Rede
        item_net = TaskItem(self.scroll, "static_ip", "Configurar IP Fixo", has_inputs=True)
        item_net.add_select("adapter_name", "Adaptador:", self.network_adapters)
        item_net.add_select("use_dhcp", "Modo IP:", ["false", "true"])
        item_net.add_input("ip", "Endereço IP:", "192.168.1.50")
        item_net.add_input("mask", "Máscara:", "255.255.255.0")
        item_net.add_input("gateway", "Gateway:", "192.168.1.1")
        item_net.add_input("dns_primary", "DNS Primário:", "8.8.8.8")
        item_net.add_input("dns_secondary", "DNS Secundário:", "1.1.1.1")
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
        self.btn_run.grid(row=3, column=0, pady=20)
        
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=4, column=0, sticky="ew", pady=10)
        self.progress.set(0)
        self.apply_selected_profile()

    def get_profile_by_name(self, name: str):
        for profile in self.controller.profiles:
            if profile.get("name") == name:
                return profile
        return None

    def _set_task_input_value(self, task_id: str, key: str, value):
        item = self.items.get(task_id)
        if not item:
            return
        widget = item.inputs.get(key)
        if not widget:
            return
        if hasattr(widget, "delete"):
            widget.delete(0, "end")
            if value is not None:
                widget.insert(0, str(value))
        elif hasattr(widget, "set"):
            widget.set(str(value))

    def apply_selected_profile(self):
        profile = self.get_profile_by_name(self.profile_var.get())
        if not profile:
            return
        self._set_task_input_value("hostname", "new_hostname", f"{profile.get('hostname_prefix', 'PC')}-01")
        self._set_task_input_value("static_ip", "use_dhcp", "true" if profile.get("use_dhcp") else "false")
        self._set_task_input_value("static_ip", "mask", profile.get("default_mask", ""))
        self._set_task_input_value("static_ip", "gateway", profile.get("default_gateway", ""))
        self._set_task_input_value("static_ip", "dns_primary", profile.get("dns_primary", ""))
        self._set_task_input_value("static_ip", "dns_secondary", profile.get("dns_secondary", ""))
        self.domain_name_override = profile.get("domain_name", "")

        profile_tasks = set(profile.get("tasks", []))
        for task_id, item in self.items.items():
            item.var.set(task_id in profile_tasks)

        selected_ids = set(profile.get("default_packages", []))
        for app_name, winget_id in settings.WINGET_PACKAGES.items():
            self.controller.software_state[app_name] = winget_id in selected_ids

    def _collect_profile_from_form(self, profile_name: str) -> dict:
        selected_tasks = [tid for tid, item in self.items.items() if item.var.get()]
        static_params = self.items["static_ip"].get_params()
        selected_package_ids = [
            package_id for app_name, package_id in settings.WINGET_PACKAGES.items()
            if self.controller.software_state.get(app_name)
        ]
        return {
            "name": profile_name,
            "hostname_prefix": (self.items["hostname"].get_params().get("new_hostname", "PC") or "PC").split("-")[0][:8],
            "domain_name": getattr(self, "domain_name_override", ""),
            "dns_primary": static_params.get("dns_primary", ""),
            "dns_secondary": static_params.get("dns_secondary", ""),
            "use_dhcp": str(static_params.get("use_dhcp", "false")).lower() == "true",
            "default_gateway": static_params.get("gateway", ""),
            "default_mask": static_params.get("mask", ""),
            "default_packages": selected_package_ids,
            "tasks": selected_tasks,
        }

    def open_save_profile_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Salvar Profile")
        modal.geometry("420x220")
        modal.grab_set()
        ctk.CTkLabel(modal, text="Nome do Profile").pack(pady=(20, 5))
        entry_name = ctk.CTkEntry(modal, width=320)
        entry_name.pack(pady=5)
        ctk.CTkLabel(modal, text="Dominio").pack(pady=(10, 5))
        entry_domain = ctk.CTkEntry(modal, width=320)
        entry_domain.insert(0, getattr(self, "domain_name_override", ""))
        entry_domain.pack(pady=5)

        def save_new_profile():
            name = entry_name.get().strip()
            if not name:
                messagebox.showwarning("Aviso", "Informe um nome para o profile.")
                return
            self.domain_name_override = entry_domain.get().strip()
            self.controller.profiles.append(self._collect_profile_from_form(name))
            if file_utils.save_json(settings.PROFILES_PATH, self.controller.profiles):
                self.refresh_profiles_ui(select_name=name)
                modal.destroy()
            else:
                messagebox.showerror("Erro", "Nao foi possivel salvar o profile.")

        ctk.CTkButton(modal, text="Salvar", command=save_new_profile).pack(pady=20)

    def open_edit_profile_modal(self):
        profile = self.get_profile_by_name(self.profile_var.get())
        if not profile:
            messagebox.showwarning("Aviso", "Selecione um profile valido para editar.")
            return
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Profile")
        modal.geometry("420x220")
        modal.grab_set()
        ctk.CTkLabel(modal, text=f"Editando: {profile.get('name')}").pack(pady=(20, 10))
        ctk.CTkLabel(modal, text="Dominio").pack(pady=(0, 5))
        entry_domain = ctk.CTkEntry(modal, width=320)
        entry_domain.insert(0, profile.get("domain_name", ""))
        entry_domain.pack(pady=5)

        def save_edit_profile():
            self.domain_name_override = entry_domain.get().strip()
            updated = self._collect_profile_from_form(profile.get("name", ""))
            for idx, current in enumerate(self.controller.profiles):
                if current.get("name") == profile.get("name"):
                    self.controller.profiles[idx] = updated
                    break
            if file_utils.save_json(settings.PROFILES_PATH, self.controller.profiles):
                self.refresh_profiles_ui(select_name=profile.get("name", ""))
                modal.destroy()
            else:
                messagebox.showerror("Erro", "Nao foi possivel atualizar o profile.")

        ctk.CTkButton(modal, text="Salvar Alteracoes", command=save_edit_profile).pack(pady=20)

    def refresh_profiles_ui(self, select_name: str = ""):
        self.profile_values = [p.get("name", "") for p in self.controller.profiles] or ["(sem perfis)"]
        self.profile_combo.configure(values=self.profile_values)
        selected = select_name if select_name in self.profile_values else self.profile_values[0]
        self.profile_var.set(selected)
        self.apply_selected_profile()

    def run_pipeline(self):
        selected_tasks = []
        gui_inputs = {
            "enable_rdp": True,
            "enable_firewall": True,
            "enable_high_performance": True,
            "enable_cleanup": True,
        }
        for tid, item in self.items.items():
            if item.var.get():
                params = item.get_params()
                selected_tasks.append(tid)
                gui_inputs.update(params)

        gui_inputs["install_packages"] = [name for name, selected_sw in self.controller.software_state.items() if selected_sw]
        gui_inputs["use_dhcp"] = str(gui_inputs.get("use_dhcp", "false")).lower() == "true"

        if not selected_tasks:
            messagebox.showwarning("Aviso", "Selecione ao menos uma tarefa.")
            return

        selected_profile = self.get_profile_by_name(self.profile_var.get()) or {}
        context = build_context(gui_inputs, selected_profile)
        self.btn_run.configure(state="disabled")
        self.controller.update_log(f"Modo de execucao: {self.mode_var.get()}")

        def run():
            pipe = ProvisioningPipeline()
            result = pipe.run(
                selected_tasks=selected_tasks,
                context=context,
                mode=self.mode_var.get(),
                callbacks={
                    "on_log": lambda m: self.update_safe(lambda: self.controller.update_log(m)),
                    "on_progress": lambda p: self.update_safe(lambda: self.update_progress(p, "Pipeline em execucao...")),
                    "on_task_start": lambda t: self.update_safe(lambda: self.controller.update_log(f"Iniciando task: {t}")),
                    "on_task_finish": lambda t, r: self.update_safe(lambda: self.controller.update_log(f"Finalizada task: {t} -> {'OK' if r.get('success') else 'ERRO'}")),
                },
            )
            self.update_safe(lambda: self.finalize_run(result))

        threading.Thread(target=run, daemon=True).start()

    def finalize_run(self, result):
        self.btn_run.configure(state="normal")
        messagebox.showinfo("Resultado", result.get("summary", "Provisionamento concluido."))

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
        self.entry_cidr = ctk.CTkEntry(scan_bar, placeholder_text="Ex: 192.168.1.0/24", width=200)
        self.entry_cidr.pack(side="left", padx=10, pady=10)
        
        self.btn_scan = ctk.CTkButton(scan_bar, text="🔍 Scan IPs em uso", width=150, command=self.run_scanner)
        self.btn_scan.pack(side="left", padx=10)

        # Sugestao de IP Control
        sug_bar = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        sug_bar.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(sug_bar, text="Sugestoes de IP Livre:").pack(side="left", padx=10)
        self.sug_var = tk.StringVar(value="")
        self.combo_sug = ctk.CTkComboBox(sug_bar, values=["(Vazio)"], variable=self.sug_var, state="readonly", width=180)
        self.combo_sug.pack(side="left", padx=10, pady=10)
        
        btn_use_ip = ctk.CTkButton(sug_bar, text="Usar IP sugerido", width=140, command=self.use_suggested_ip)
        btn_use_ip.pack(side="left", padx=10)
        
        # Results View
        self.results_box = ctk.CTkTextbox(self, height=350)
        self.results_box.grid(row=3, column=0, sticky="nsew", pady=10)
        self.results_box.insert("end", "Aperte 'Scan IPs em uso' para detectar a subrede atual e buscar IPs livres/ocupados...")

    def use_suggested_ip(self):
        ip = self.sug_var.get()
        if not ip or ip == "(Vazio)" or "Erro" in ip:
            messagebox.showwarning("Aviso", "Nenhum IP valido selecionado.")
            return
            
        # Tenta injetar na aba de Provisionamento
        prov_frame = self.controller.get_frame("provisioning")
        if prov_frame:
            # Seta o IP da entry "static_ip" item
            prov_frame._set_task_input_value("static_ip", "ip", ip)
            messagebox.showinfo("Sucesso", f"IP {ip} preenchido na aba de Provisionamento.")
        else:
            # Caso a aba nao esteja criada/instanciada ou a logica do get_frame falhe
            # Podemos tentar forcando a troca de aba primeiro
            self.controller.select_frame("provisioning")
            self.after(200, lambda: self._delayed_inject(ip))

    def _delayed_inject(self, ip):
        prov_frame = self.controller.get_frame("provisioning")
        if prov_frame:
            prov_frame._set_task_input_value("static_ip", "ip", ip)
            prov_frame._set_task_input_value("static_ip", "use_dhcp", "false")
            messagebox.showinfo("Sucesso", f"IP {ip} inserido!")

    def run_scanner(self):
        cidr = self.entry_cidr.get()
            
        self.btn_scan.configure(state="disabled")
        self.combo_sug.configure(values=["Carregando..."])
        self.sug_var.set("Carregando...")
        self.results_box.delete("1.0", "end")
        
        target_str = f" em {cidr}" if cidr else " na subrede atual"
        self.results_box.insert("end", f"Iniciando scan{target_str}...\nIsso pode levar alguns segundos dependendo da rede.\n")
        
        def do_scan():
            res = ip_scanner.scan_network(cidr if cidr else None)
            if self.winfo_exists():
                self.after(0, lambda: self.show_results(res))
            
        threading.Thread(target=do_scan, daemon=True).start()

    def show_results(self, res):
        self.btn_scan.configure(state="normal")
        self.results_box.delete("1.0", "end")
        if "error" in res:
            self.results_box.insert("end", f"Erro: {res['error']}")
            self.combo_sug.configure(values=["(Erro)"])
            self.sug_var.set("(Erro)")
            return
            
        self.results_box.insert("end", f"=== Resultado do Scan ({res['network']}) ===\n")
        
        ocupados = res.get('occupied', [])
        livres = res.get('free', [])
        sugestoes = res.get('suggestions', [])
        
        self.results_box.insert("end", f"IPs Ocupados Encontrados: {len(ocupados)}\n")
        self.results_box.insert("end", f"IPs Livres (estimativa): {len(livres)}\n\n")
        
        self.results_box.insert("end", "[ TABELA DE IPS OCUPADOS ]\n")
        for i, ip in enumerate(ocupados, 1):
            self.results_box.insert("end", f"{i:03d} - {ip}\n")
            
        if sugestoes:
            self.combo_sug.configure(values=sugestoes)
            self.sug_var.set(sugestoes[0])
            self.results_box.insert("end", f"\n[ SUGESTOES DE IPS LIVRES ]\n")
            for ip in sugestoes:
                self.results_box.insert("end", f"  -> {ip}\n")
        else:
            self.combo_sug.configure(values=["(Nenhuma)"])
            self.sug_var.set("(Nenhuma)")

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
        
        # Grid definition
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Lista de softwares (Esquerda)
        list_frame = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        self.scroll = ctk.CTkScrollableFrame(list_frame, height=400, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.sw_vars = {}
        for name in settings.WINGET_PACKAGES.keys():
            # Carregar estado persistente do controller
            initial_val = self.controller.software_state.get(name, False)
            var = tk.BooleanVar(value=initial_val)
            
            cb = ctk.CTkCheckBox(self.scroll, text=name, variable=var, 
                                 command=lambda n=name, v=var: self.save_state(n, v))
            cb.pack(anchor="w", padx=20, pady=5)
            self.sw_vars[name] = var

        self.btn_install = ctk.CTkButton(list_frame, text="📦 Instalar Selecionados", command=self.install_sw)
        self.btn_install.pack(pady=20)
        
        # Logs em tempo real (Direita)
        log_frame = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        log_frame.grid(row=1, column=1, sticky="nsew")
        ctk.CTkLabel(log_frame, text="Progresso de Instalação", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.sw_log_area = ctk.CTkTextbox(log_frame, state="disabled")
        self.sw_log_area.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def save_state(self, name, var):
        """Salva o estado no controller para não perder ao trocar de aba."""
        self.controller.software_state[name] = var.get()
        
    def add_sw_log(self, msg):
        self.sw_log_area.configure(state="normal")
        self.sw_log_area.insert("end", f"{msg}\n")
        self.sw_log_area.see("end")
        self.sw_log_area.configure(state="disabled")
        self.controller.update_log(msg) # Envia tambem para o log geral

    def install_sw(self):
        # Mapeia nome selecionado para ID do pacote winget
        to_install = [settings.WINGET_PACKAGES[name] for name, var in self.sw_vars.items() if var.get()]
        if not to_install:
            messagebox.showwarning("Aviso", "Selecione ao menos um software.")
            return
            
        self.btn_install.configure(state="disabled")
        self.sw_log_area.configure(state="normal")
        self.sw_log_area.delete("1.0", "end")
        self.sw_log_area.configure(state="disabled")
        self.add_sw_log("Iniciando instalacao em lote...")
        
        from app.services.software_installer import install_multiple
        
        def run():
            res = install_multiple(to_install)
            if self.winfo_exists():
                self.after(0, lambda: self.btn_install.configure(state="normal"))
                msg = "Sucesso!" if res["success"] else "Concluido com erros."
                self.after(0, lambda: self.add_sw_log(f"\nFinal: {msg}"))
                self.after(0, lambda: messagebox.showinfo("Resultado", msg))
            
        threading.Thread(target=run, daemon=True).start()

class SecurityFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Segurança do Sistema", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # 1. Microsoft Defender
        def_box = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        def_box.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        def_box.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(def_box, text="🛡️ Microsoft Defender", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        self.lbl_def_status = ctk.CTkLabel(def_box, text="Verificando status...", text_color=settings.TEXT_MUTED)
        self.lbl_def_status.grid(row=0, column=1, padx=20, pady=15, sticky="e")
        
        btn_def_frame = ctk.CTkFrame(def_box, fg_color="transparent")
        btn_def_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        
        ctk.CTkButton(btn_def_frame, text="Atualizar Definições", command=self.update_defender_signatures, width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_def_frame, text="Verificação Rápida", command=self.run_defender_scan, width=150).pack(side="left", padx=5)

        # 2. Firewall do Windows (Granular)
        fw_box = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        fw_box.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(fw_box, text="🔥 Firewall do Windows", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))
        
        profiles = [("Domain", "🌐 Domínio"), ("Private", "🏠 Privada"), ("Public", "📋 Pública")]
        self.fw_btns = {}
        
        for pid, label in profiles:
            f = ctk.CTkFrame(fw_box, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=label).pack(side="left")
            
            btn = ctk.CTkButton(f, text="Verificando...", width=120)
            btn.pack(side="right", padx=5)
            self.fw_btns[pid] = btn

        # 3. Acesso Remoto e Outros
        extra_box = ctk.CTkFrame(self, fg_color=settings.BG_CARD)
        extra_box.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(extra_box, text="Acesso Remoto (RDP)").pack(side="left", padx=20, pady=20)
        ctk.CTkButton(extra_box, text="Habilitar RDP", width=120, command=lambda: self.run_task("rdp_on")).pack(side="right", padx=20)

        # Inicia atualização de status
        self.update_status_loop()

    def update_status_loop(self):
        """Atualiza os indicadores de status na interface."""
        if not self.winfo_exists(): return

        # 1. Update Defender Status
        from app.services.defender_service import get_defender_status
        def_status = get_defender_status()
        if def_status:
            enabled = def_status.get("RealTimeProtectionEnabled", False)
            text = "PROTEÇÃO ATIVA" if enabled else "PROTEÇÃO DESATIVADA"
            color = settings.SUCCESS_COLOR if enabled else settings.ERROR_COLOR
            self.lbl_def_status.configure(text=text, text_color=color)
        
        # 2. Update Firewall Buttons
        from app.services.firewall_service import get_firewall_status
        fw_status_list = get_firewall_status()
        # Converte lista de dicts para dict simples
        fw_map = {item['Name']: item['Enabled'] for item in fw_status_list} if isinstance(fw_status_list, list) else {}

        for profile, btn in self.fw_btns.items():
            is_on = fw_map.get(profile, False)
            btn_text = "Desativar" if is_on else "Ativar"
            btn_color = "#c0392b" if is_on else "#27ae60"
            btn_hover = "#a93226" if is_on else "#229954"
            
            btn.configure(text=btn_text, fg_color=btn_color, hover_color=btn_hover,
                         command=lambda p=profile, s=is_on: self.toggle_fw(p, not s))
        
        if self.winfo_exists():
            self.after(5000, self.update_status_loop) # Atualiza a cada 5s

    def toggle_fw(self, profile, enabled):
        from app.services.firewall_service import set_firewall_profile_status
        def run():
            res = set_firewall_profile_status(profile, enabled)
            if self.winfo_exists():
                self.after(0, lambda: Toast(res["message"], "success" if res["success"] else "error"))
                self.after(500, self.update_status_loop) # Força refresh rápido
        threading.Thread(target=run, daemon=True).start()

    def update_defender_signatures(self):
        from app.services.defender_service import update_defender
        def run():
            self.controller.update_log("Atualizando definições do Defender...")
            res = update_defender()
            if self.winfo_exists():
                self.after(0, lambda: Toast(res["message"], "success" if res["success"] else "error"))
        threading.Thread(target=run, daemon=True).start()

    def run_defender_scan(self):
        from app.services.defender_service import run_quick_scan
        def run():
            self.controller.update_log("Iniciando verificação rápida do Defender...")
            res = run_quick_scan()
            if self.winfo_exists():
                self.after(0, lambda: Toast(res["message"], "success" if res["success"] else "error"))
        threading.Thread(target=run, daemon=True).start()

    def run_task(self, task_id):
        from app.modules.task_registry import get_task_function
        func = get_task_function(task_id)
        if func:
            def run():
                res = func()
                if self.winfo_exists():
                    self.after(0, lambda: Toast(res["message"], "success" if res["success"] else "error"))
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
