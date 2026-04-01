import platform
import subprocess
import socket
import threading
import ipaddress
import re
import logging
import time

logger = logging.getLogger(__name__)

def get_current_network_info():
    """Retorna IP, Máscara, Gateway e Nome do Adaptador (via PowerShell/ipconfig ou socket)."""
    # Simplificado usando psutil se disponivel ou socket (dummy implementation for demonstration or subprocess)
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, encoding='cp850', errors='replace')
            output = result.stdout
            
            adapter_name = "Ethernet"
            ip = ""
            mask = ""
            gateway = ""
            
            # Very basic parse
            current_adapter = ""
            for line in output.split('\n'):
                line = line.strip()
                if line.endswith(':'):
                    current_adapter = line[:-1]
                if "IPv4" in line or "IP Address" in line:
                    match = re.search(r'\d+\.\d+\.\d+\.\d+', line)
                    if match and not ip:
                        ip = match.group()
                        adapter_name = current_adapter
                if "Subnet Mask" in line or "M\u00e1scara de Sub-rede" in line or "Máscara" in line:
                    match = re.search(r'\d+\.\d+\.\d+\.\d+', line)
                    if match and not mask:
                        mask = match.group()
                if "Default Gateway" in line or "Gateway Padr\u00e3o" in line or "Gateway Padrão" in line:
                    match = re.search(r'\d+\.\d+\.\d+\.\d+', line)
                    if match and not gateway:
                        gateway = match.group()
                        
            return {
                "ip": ip or "127.0.0.1",
                "mask": mask or "255.255.255.0",
                "gateway": gateway or "127.0.0.1",
                "adapter_name": adapter_name
            }
    except Exception as e:
        logger.error(f"Erro ao obter rede atual: {e}")
        
    return {"ip": "127.0.0.1", "mask": "255.255.255.0", "gateway": "", "adapter_name": "Loopback"}

def calculate_subnet_range(ip, mask):
    """Calcula a lista de IPs a partir de ip e mask."""
    try:
        network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
        return [str(ip) for ip in network.hosts()]
    except Exception as e:
        logger.error(f"Erro ao calcular range de subrede: {e}")
        return []

def ping_ip(ip):
    """Retorna True se o IP responder ao ping."""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        # ping rapido (1 pacote, timeout 300ms)
        command = ["ping", param, "1", "-w", "300", ip] if platform.system().lower() == "windows" else ["ping", param, "1", "-W", "1", ip]
        res = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except Exception:
        return False

def scan_network_threads(range_ips):
    """Realiza ping paralelo nos IPs."""
    active_ips = []
    lock = threading.Lock()
    
    def worker(ips_chunk):
        for ip in ips_chunk:
            if ping_ip(ip):
                with lock:
                    active_ips.append(ip)

    threads = []
    chunk_size = max(1, len(range_ips) // 50)
    
    for i in range(0, len(range_ips), chunk_size):
        chunk = range_ips[i:i + chunk_size]
        t = threading.Thread(target=worker, args=(chunk,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    return active_ips

def get_arp_table():
    """Recupera a tabela ARP e suas entradas."""
    try:
        res = subprocess.run(["arp", "-a"], capture_output=True, text=True, encoding='cp850', errors='replace')
        ips = []
        for line in res.stdout.split('\n'):
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)', line)
            if match:
                ips.append(match.group(1))
        return list(set(ips))
    except Exception as e:
        logger.error(f"Erro no arp table: {e}")
        return []

def merge_results(ping_results, arp_results):
    """Unifica e remove duplicatas."""
    return sorted(list(set(ping_results + arp_results)), key=lambda ip: socket.inet_aton(ip))

def suggest_free_ips(occupied_ips, range_ips):
    """Retorna os primeiros 10 IPs nao ocupados, ignorando os ultimos da rede ou broadcast."""
    free = []
    occupied_set = set(occupied_ips)
    for ip_str in range_ips:
        if ip_str not in occupied_set:
            if not ip_str.endswith(".1") and not ip_str.endswith(".254") and not ip_str.endswith(".255"):
                free.append(ip_str)
        if len(free) >= 10:
            break
    return free

def scan_network(cidr_or_range=None):
    """Funcao chamada pelo GUI. Retorna dicionário com os resultados."""
    try:
        net_info = get_current_network_info()
        base_ip = net_info["ip"]
        mask = net_info["mask"]
        
        # Para forçar no range correto
        if cidr_or_range and "/" in cidr_or_range:
            try:
                network = ipaddress.IPv4Network(cidr_or_range, strict=False)
                range_ips = [str(ip) for ip in network.hosts()]
            except:
                range_ips = calculate_subnet_range(base_ip, mask)
        else:
            range_ips = calculate_subnet_range(base_ip, mask)
        
        if not range_ips:
            return {"error": "Não foi possível calcular o range."}

        # Rodar scan e arp
        ping_ativos = scan_network_threads(range_ips)
        arp_ativos = get_arp_table()
        
        # Alguns ARPs podem estar fora do range, mas vamos focar no range de IP atual
        arp_in_range = [ip for ip in arp_ativos if ip in range_ips]
        
        ocupados = merge_results(ping_ativos, arp_in_range)
        livres = [ip for ip in range_ips if ip not in ocupados]
        sugestoes = suggest_free_ips(ocupados, range_ips)
        
        return {
            "network": f"{base_ip}/{mask}",
            "occupied": ocupados,
            "free": livres,
            "suggestions": sugestoes,
            "net_info": net_info
        }
    except Exception as e:
        logger.error(f"Failed scan_network: {e}")
        return {"error": str(e)}
