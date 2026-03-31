"""
Criptografia simples para dados sensíveis locais.
Usa Fernet (cryptography) para criptografar/descriptografar strings.

IMPORTANTE: A chave é derivada do volume serial do disco — por isso
os dados só podem ser lidos na mesma máquina que os criou.
Senhas NÃO devem ser persistidas. Use este módulo apenas para
dados de configuração sensíveis (ex: pre-shared keys, tokens).
"""

import os
import base64
import hashlib
import logging
import subprocess

logger = logging.getLogger("WindowsProvisioningAssistant")

try:
    from cryptography.fernet import Fernet, InvalidToken
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    logger.warning("[Encryption] Pacote 'cryptography' não instalado. Criptografia desabilitada.")


def _get_machine_key() -> bytes:
    """Gera uma chave Fernet baseada no serial do volume C:."""
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", "(Get-Volume -DriveLetter C).UniqueId"],
            capture_output=True, text=True, timeout=5
        )
        seed = result.stdout.strip() or "DefaultWindowsProvisioningKey2026"
    except Exception:
        seed = "DefaultWindowsProvisioningKey2026"

    # Deriva 32 bytes via SHA-256 e converte para base64url (formato Fernet)
    raw = hashlib.sha256(seed.encode()).digest()
    return base64.urlsafe_b64encode(raw)


def encrypt(plaintext: str) -> str:
    """Criptografa uma string. Retorna a string criptografada em base64 ou a original se sem crypto."""
    if not _CRYPTO_AVAILABLE or not plaintext:
        return plaintext
    try:
        f = Fernet(_get_machine_key())
        return f.encrypt(plaintext.encode()).decode()
    except Exception as e:
        logger.error(f"[Encryption] Erro ao criptografar: {e}")
        return plaintext


def decrypt(ciphertext: str) -> str:
    """Descriptografa uma string. Retorna a string decriptografada ou a original se falhar."""
    if not _CRYPTO_AVAILABLE or not ciphertext:
        return ciphertext
    try:
        f = Fernet(_get_machine_key())
        return f.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception) as e:
        logger.warning(f"[Encryption] Falha ao descriptografar (token inválido ou chave diferente): {e}")
        return ciphertext


def is_available() -> bool:
    """Retorna True se o módulo cryptography está disponível."""
    return _CRYPTO_AVAILABLE
