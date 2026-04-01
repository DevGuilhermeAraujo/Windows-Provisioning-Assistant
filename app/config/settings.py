"""Configurações globais e de interface do Windows Provisioning Assistant v2."""

APP_NAME = "Windows Provisioning Assistant"
APP_VERSION = "2.0.0"
DB_NAME = "provisioning.db"

# Temas UI (CustomTkinter)
APPEARANCE_MODE = "dark"
COLOR_THEME = "blue"

# Paleta de cores corporativa
SUCCESS_COLOR   = "#27ae60"
ERROR_COLOR     = "#e74c3c"
WARNING_COLOR   = "#f39c12"
INFO_COLOR      = "#2980b9"
ACCENT_COLOR    = "#1a73e8"
BG_DARK         = "#1e1e2e"
BG_CARD         = "#2a2a3d"
TEXT_MUTED      = "#a0a0b0"

# Diretórios
LOG_PATH        = "logs/app.log"
OUTPUT_REPORTS_PATH = "output/reports"
LOG_FILE        = LOG_PATH
REPORTS_DIR     = OUTPUT_REPORTS_PATH
EXPORTS_DIR     = "output/exports"
BACKUPS_DIR     = "output/backups"
DB_PATH         = "output/provisioning.db"
PROFILES_PATH   = "app/config/profiles.json"

# Configurações de Janela
WINDOW_WIDTH    = 1280
WINDOW_HEIGHT   = 820

# Scanner de Rede
SCAN_TIMEOUT    = 0.3   # segundos por ping
SCAN_THREADS    = 100   # threads paralelas

# Softwares disponíveis para instalação via winget
WINGET_PACKAGES = {
    "Google Chrome":    "Google.Chrome",
    "7-Zip":            "7zip.7zip",
    "AnyDesk":          "AnyDeskSoftwareGmbH.AnyDesk",
    "VS Code":          "Microsoft.VisualStudioCode",
    "Notepad++":        "Notepad++.Notepad++",
    "Git":              "Git.Git",
    "VLC":              "VideoLAN.VLC",
    "Adobe Reader":     "Adobe.Acrobat.Reader.64-bit",
    "TeamViewer":       "TeamViewer.TeamViewer",
    "WinRAR":           "RARLab.WinRAR",
}
