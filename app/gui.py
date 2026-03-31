import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
import threading
from datetime import datetime

# Importações internas
from .utils.system_info import get_current_hostname, get_network_adapters
from .utils.logger import setup_logger
from .utils.validators import validate_ip, validate_hostname, validate_domain
from .services.hostname_service import rename_computer
from .services.network_service import set_dhcp, set_static_ip
from .services.domain_service import join_domain
from .services.user_service import create_local_admin
from .reports.report_generator import generate_report
from .config import settings

class App(ctk.CTk):
    def __init__(self, is_admin: bool = True):
        super().__init__()

        self.is_admin = is_admin

        # Título com indicação de modo
        admin_label = "" if is_admin else " [MODO LIMITADO - Sem Admin]"
        self.title(f"{settings.APP_NAME} v{settings.APP_VERSION}{admin_label}")
        self.geometry(f"{settings.WINDOW_WIDTH}x{settings.WINDOW_HEIGHT}")

        # Layout principal: 2 colunas, 3 linhas (aviso, conteúdo, log)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)  # row 1 = conteúdo principal

        # Variáveis de estado
        self.execution_log_data = []

        # Inicializar Logger SEM callback de GUI ainda
        # O callback será adicionado depois que o log_textbox for criado
        self.logger = setup_logger()

        # --- BANNER DE AVISO (somente sem admin) ---
        if not self.is_admin:
            self.warning_bar = ctk.CTkFrame(self, fg_color="#7d3c00", height=35, corner_radius=0)
            self.warning_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
            self.warning_bar.grid_propagate(False)
            ctk.CTkLabel(
                self.warning_bar,
                text="⚠️  Executando SEM privilégios de Administrador. Ações do sistema irão falhar. Feche e rode como Admin.",
                text_color="#FFD700",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(side="left", padx=10, pady=5)

        # --- SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Windows\nProvisioning", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_hostname = ctk.CTkButton(self.sidebar_frame, text="Nome do PC", command=lambda: self.select_frame("hostname"))
        self.btn_hostname.grid(row=1, column=0, padx=20, pady=10)

        self.btn_network = ctk.CTkButton(self.sidebar_frame, text="Rede", command=lambda: self.select_frame("network"))
        self.btn_network.grid(row=2, column=0, padx=20, pady=10)

        self.btn_domain = ctk.CTkButton(self.sidebar_frame, text="Domínio AD", command=lambda: self.select_frame("domain"))
        self.btn_domain.grid(row=3, column=0, padx=20, pady=10)

        self.btn_user = ctk.CTkButton(self.sidebar_frame, text="Usuário Local", command=lambda: self.select_frame("user"))
        self.btn_user.grid(row=4, column=0, padx=20, pady=10)

        self.btn_report = ctk.CTkButton(self.sidebar_frame, text="Gerar Relatório", fg_color="transparent", border_width=2, command=self.action_generate_report)
        self.btn_report.grid(row=5, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Modo:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_optionemenu.set("Dark")

        # --- MAIN FRAMES ---
        self.frame_hostname = self.create_hostname_frame()
        self.frame_network = self.create_network_frame()
        self.frame_domain = self.create_domain_frame()
        self.frame_user = self.create_user_frame()

        # --- LOG SECTION (BOTTOM) ---
        self.log_frame = ctk.CTkFrame(self, height=200)
        self.log_frame.grid(row=2, column=1, sticky="nsew", padx=20, pady=(0, 20))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)

        self.log_header = ctk.CTkLabel(self.log_frame, text="Logs em tempo real", font=ctk.CTkFont(size=14, weight="bold"))
        self.log_header.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.log_textbox = ctk.CTkTextbox(self.log_frame, state="disabled", font=("Consolas", 12))
        self.log_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.status_label = ctk.CTkLabel(self.log_frame, text="Status: Aguardando ação...", text_color="gray")
        self.status_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        # Agora que o log_textbox existe, adiciona o callback de GUI ao logger
        from .utils.logger import GUILogHandler
        import logging
        gui_handler = GUILogHandler(self.update_log_box)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(gui_handler)

        # Iniciar no frame de hostname
        self.select_frame("hostname")

    # --- FRAME FACTORIES ---

    def create_hostname_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        
        label = ctk.CTkLabel(frame, text="Alterar Nome do Computador", font=ctk.CTkFont(size=24, weight="bold"))
        label.grid(row=0, column=0, padx=20, pady=40)
        
        # Nome Atual
        current_name = get_current_hostname()
        self.lbl_current_name = ctk.CTkLabel(frame, text=f"Nome Atual: {current_name}", font=ctk.CTkFont(size=16))
        self.lbl_current_name.grid(row=1, column=0, padx=20, pady=10)
        
        # Novo Nome
        self.entry_new_hostname = ctk.CTkEntry(frame, placeholder_text="Novo Hostname (ex: EST-ADM-01)", width=300)
        self.entry_new_hostname.grid(row=2, column=0, padx=20, pady=20)
        
        btn = ctk.CTkButton(frame, text="Aplicar Alteração", command=self.action_rename_computer)
        btn.grid(row=3, column=0, padx=20, pady=20)
        
        return frame

    def create_network_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.grid_columnconfigure(1, weight=1)

        label = ctk.CTkLabel(frame, text="Configuração de Rede", font=ctk.CTkFont(size=24, weight="bold"))
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=40)

        # Seleção de Interface - lida com falha silenciosa se PS não responder
        ctk.CTkLabel(frame, text="Interface:").grid(row=1, column=0, padx=20, pady=10, sticky="e")
        try:
            self.adapters = get_network_adapters()
            adapter_names = [a['Name'] for a in self.adapters] if self.adapters else ["Nenhum adaptador encontrado"]
        except Exception:
            self.adapters = []
            adapter_names = ["Erro ao listar adaptadores"]
        self.option_adapter = ctk.CTkOptionMenu(frame, values=adapter_names, width=300)
        self.option_adapter.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        
        # Checkbox DHCP
        self.check_dhcp = ctk.CTkCheckBox(frame, text="Usar DHCP", command=self.toggle_network_fields)
        self.check_dhcp.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        self.check_dhcp.select()
        
        # Campos de IP Estático
        self.entry_ip = ctk.CTkEntry(frame, placeholder_text="IP (Ex: 192.168.1.50)", width=300)
        self.entry_mask = ctk.CTkEntry(frame, placeholder_text="Máscara (Ex: 255.255.255.0)", width=300)
        self.entry_gw = ctk.CTkEntry(frame, placeholder_text="Gateway", width=300)
        self.entry_dns1 = ctk.CTkEntry(frame, placeholder_text="DNS Primário", width=300)
        self.entry_dns2 = ctk.CTkEntry(frame, placeholder_text="DNS Secundário", width=300)
        
        self.network_entries = [self.entry_ip, self.entry_mask, self.entry_gw, self.entry_dns1, self.entry_dns2]
        for i, entry in enumerate(self.network_entries):
            entry.grid(row=3+i, column=1, padx=20, pady=5, sticky="w")
            entry.configure(state="disabled") # Começa desabilitado por causa do DHCP
            
        btn = ctk.CTkButton(frame, text="Aplicar Configuração de Rede", command=self.action_configure_network)
        btn.grid(row=8, column=1, padx=20, pady=30, sticky="w")
        
        return frame

    def create_domain_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(frame, text="Adicionar ao Domínio AD", font=ctk.CTkFont(size=24, weight="bold"))
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=40)
        
        ctk.CTkLabel(frame, text="Domínio:").grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.entry_domain = ctk.CTkEntry(frame, placeholder_text="corp.local", width=300)
        self.entry_domain.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        
        ctk.CTkLabel(frame, text="Usuário Admin:").grid(row=2, column=0, padx=20, pady=10, sticky="e")
        self.entry_domain_user = ctk.CTkEntry(frame, placeholder_text="Administrator", width=300)
        self.entry_domain_user.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        
        ctk.CTkLabel(frame, text="Senha:").grid(row=3, column=0, padx=20, pady=10, sticky="e")
        self.entry_domain_pass = ctk.CTkEntry(frame, show="*", width=300)
        self.entry_domain_pass.grid(row=3, column=1, padx=20, pady=10, sticky="w")
        
        btn = ctk.CTkButton(frame, text="Entrar no Domínio", command=self.action_join_domain)
        btn.grid(row=4, column=1, padx=20, pady=30, sticky="w")
        
        return frame

    def create_user_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(frame, text="Criar Usuário Local Admin", font=ctk.CTkFont(size=24, weight="bold"))
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=40)
        
        ctk.CTkLabel(frame, text="Nome de Usuário:").grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.entry_local_user = ctk.CTkEntry(frame, placeholder_text="suporte.local", width=300)
        self.entry_local_user.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        
        ctk.CTkLabel(frame, text="Senha:").grid(row=2, column=0, padx=20, pady=10, sticky="e")
        self.entry_local_pass = ctk.CTkEntry(frame, show="*", width=300)
        self.entry_local_pass.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        
        btn = ctk.CTkButton(frame, text="Criar Usuário Administrador", command=self.action_create_user)
        btn.grid(row=3, column=1, padx=20, pady=30, sticky="w")
        
        return frame

    # --- UI HELPERS ---

    def select_frame(self, name):
        # Reset colors of sidebar buttons
        self.btn_hostname.configure(fg_color=("gray75", "gray25") if name != "hostname" else ["#3B8ED0", "#1F6AA5"])
        self.btn_network.configure(fg_color=("gray75", "gray25") if name != "network" else ["#3B8ED0", "#1F6AA5"])
        self.btn_domain.configure(fg_color=("gray75", "gray25") if name != "domain" else ["#3B8ED0", "#1F6AA5"])
        self.btn_user.configure(fg_color=("gray75", "gray25") if name != "user" else ["#3B8ED0", "#1F6AA5"])

        # Esconder todos os frames
        self.frame_hostname.grid_forget()
        self.frame_network.grid_forget()
        self.frame_domain.grid_forget()
        self.frame_user.grid_forget()

        # Mostrar o selecionado (row=1 para respeitar o banner no row=0)
        if name == "hostname":
            self.frame_hostname.grid(row=1, column=1, sticky="nsew")
        elif name == "network":
            self.frame_network.grid(row=1, column=1, sticky="nsew")
        elif name == "domain":
            self.frame_domain.grid(row=1, column=1, sticky="nsew")
        elif name == "user":
            self.frame_user.grid(row=1, column=1, sticky="nsew")

    def toggle_network_fields(self):
        state = "disabled" if self.check_dhcp.get() else "normal"
        for entry in self.network_entries:
            entry.configure(state=state)

    def update_log_box(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        # Também guarda para o relatório
        self.execution_log_data.append(message.strip())

    def set_status(self, text, color="gray"):
        self.status_label.configure(text=f"Status: {text}", text_color=color)

    def change_appearance_mode(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    # --- ACTIONS (THREADED) ---

    def run_in_thread(self, target, *args):
        self.set_status("Executando...", settings.INFO_COLOR)
        def wrapper():
            try:
                target(*args)
            except Exception as e:
                self.logger.error(f"Erro inesperado: {e}")
                self.set_status("Erro!", settings.ERROR_COLOR)
        threading.Thread(target=wrapper, daemon=True).start()

    def action_rename_computer(self):
        new_name = self.entry_new_hostname.get().strip()
        if not new_name:
            messagebox.showwarning("Aviso", "O nome não pode estar vazio.")
            return
        
        def task():
            res = rename_computer(new_name)
            if res["success"]:
                self.set_status("Sucesso! Reinicie o PC.", settings.SUCCESS_COLOR)
                messagebox.showinfo("Sucesso", res["message"])
            else:
                self.set_status("Falha ao renomear.", settings.ERROR_COLOR)
                messagebox.showerror("Erro", res["message"])
                
        self.run_in_thread(task)

    def action_configure_network(self):
        adapter = self.option_adapter.get()
        is_dhcp = self.check_dhcp.get()
        
        def task():
            if is_dhcp:
                res = set_dhcp(adapter)
            else:
                ip = self.entry_ip.get().strip()
                mask = self.entry_mask.get().strip()
                gw = self.entry_gw.get().strip()
                dns = [self.entry_dns1.get().strip(), self.entry_dns2.get().strip()]
                res = set_static_ip(adapter, ip, mask, gw if gw else None, dns)
                
            if res["success"]:
                self.set_status("Rede configurada.", settings.SUCCESS_COLOR)
                messagebox.showinfo("Sucesso", res["message"])
            else:
                self.set_status("Erro na rede.", settings.ERROR_COLOR)
                messagebox.showerror("Erro", res["message"])

        self.run_in_thread(task)

    def action_join_domain(self):
        domain = self.entry_domain.get().strip()
        user = self.entry_domain_user.get().strip()
        pwd = self.entry_domain_pass.get().strip()
        
        if not domain or not user or not pwd:
            messagebox.showwarning("Campos vazios", "Preencha todos os campos do domínio.")
            return

        def task():
            res = join_domain(domain, user, pwd)
            if res["success"]:
                self.set_status("Ingressou no domínio. Reinicie.", settings.SUCCESS_COLOR)
                messagebox.showinfo("Sucesso", res["message"])
            else:
                self.set_status("Erro no domínio.", settings.ERROR_COLOR)
                messagebox.showerror("Erro", res["message"])

        self.run_in_thread(task)

    def action_create_user(self):
        user = self.entry_local_user.get().strip()
        pwd = self.entry_local_pass.get().strip()
        
        if not user or not pwd:
            messagebox.showwarning("Campos vazios", "Preencha usuário e senha.")
            return

        def task():
            res = create_local_admin(user, pwd)
            if res["success"]:
                self.set_status("Usuário criado.", settings.SUCCESS_COLOR)
                messagebox.showinfo("Sucesso", res["message"])
            else:
                self.set_status("Erro ao criar usuário.", settings.ERROR_COLOR)
                messagebox.showerror("Erro", res["message"])

        self.run_in_thread(task)

    def action_generate_report(self):
        # Coletar dados simplificados para o relatório
        report_data = {
            "hostname_atual": get_current_hostname(),
            "logs_execucao": self.execution_log_data
        }
        res = generate_report(report_data)
        if res["success"]:
            messagebox.showinfo("Relatório", f"Relatório salvo em:\n{res['filepath']}")
        else:
            messagebox.showerror("Erro", "Falha ao gerar relatório.")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
