import re
import ipaddress

def validate_ip(ip_str: str) -> bool:
    """Valida se uma string é um endereço IP IPv4 válido."""
    try:
        ipaddress.IPv4Address(ip_str)
        return True
    except ValueError:
        return False

def validate_mask(mask_str: str) -> bool:
    """Valida se uma string é uma máscara de sub-rede válida."""
    try:
        # Verifica se o IP é válido como máscara (ex: 255.255.255.0)
        ipaddress.IPv4Address(mask_str)
        return True
    except ValueError:
        return False

def validate_hostname(hostname: str) -> bool:
    """Valida o nome do computador de acordo com as regras NetBIOS/DNS."""
    # Regras básicas: Letras, números e hífens. Não pode começar ou terminar com hífen.
    # Máximo de 15 caracteres (NetBIOS) ou 63 (DNS). 
    # Por segurança corporativa, muitas vezes limita-se a 15.
    if not hostname:
        return False
    if len(hostname) > 15:
        return False
    # Apenas letras, números e hífen
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$ '
    # Versão simplificada regex: ^[a-zA-Z0-9-]+$ 
    # Mas evitando hífens no início e fim
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,13}[a-zA-Z0-9])?$', hostname):
        return False
    return True

def validate_domain(domain: str) -> bool:
    """Valida o nome de um domínio (ex: corp.local)."""
    if not domain:
        return False
    # Regras básicas para nomes de domínio
    pattern = r'^([a-zA-Z0-9][a-zA-Z0-9-]*\.)+[a-zA-Z]{2,}$'
    # Aceitando formatos .local
    if '.' not in domain:
        return False
    return bool(re.match(r'^[a-zA-Z0-9.-]+$', domain))

def validate_username(username: str) -> bool:
    """Valida nome de usuário local."""
    if not username:
        return False
    # Não pode conter caracteres especiais: / \ [ ] : ; | = , + * ? < >
    invalid_chars = r'[/\\[\]:;|=,+*?<>]'
    if re.search(invalid_chars, username):
        return False
    return len(username) <= 20
