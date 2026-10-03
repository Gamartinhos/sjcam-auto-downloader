import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import subprocess

CAMERA_URL = "http://192.168.1.254/DCIM/Movie/"
DOWNLOAD_DIR = "./videos_sjcam/"
EXPECTED_WIFI_PREFIX = "C100+"

def check_wifi():
    print("A verificar ligação Wi-Fi...")
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            if "SSID" in line and "BSSID" not in line:
                parts = line.split(":")
                if len(parts) > 1:
                    ssid = parts[1].strip()
                    if ssid.startswith(EXPECTED_WIFI_PREFIX) or ssid == "C100+_GC140a028a71bb":
                        print(f"✓ Ligado à rede da câmara: {ssid}")
                        return True
                    else:
                        print(f"⚠ Aviso: Está ligado à rede '{ssid}', mas a rede esperada é 'C100+_GC140a028a71bb' (ou similar).")
                        return False
        print("⚠ Aviso: Não foi possível detetar o SSID atual.")
        return False
    except Exception as e:
        print(f"Erro ao verificar Wi-Fi: {e}")
        return False

def get_video_links(url):
    print(f"[{time.strftime('%H:%M:%S')}] A aceder à câmara em {url} ...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao ligar à câmara: {e}")
        print("Certifique-se de que está ligado à rede Wi-Fi da SJCAM.")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Simple HTTP file servers usually have <a> tags linking to the files
    links = soup.find_all('a')
    video_files = []
    for link in links:
        href = link.get('href')
        if href and href.upper().endswith('.MP4'):
            # Some servers include the full path, some just the filename
            video_files.append(href)
            
    # Remove duplicates preserving order
    video_files = list(dict.fromkeys(video_files))
    print(f"Encontrados {len(video_files)} vídeos na câmara.")
    return video_files

def download_file(file_url, dest_path, retries=3):
    """Downloads a file with a progress bar and resume capability."""
    
    for attempt in range(retries):
        try:
            # Check if file exists to resume or skip
            headers = {}
            file_mode = 'ab'
            initial_pos = 0
            
            if os.path.exists(dest_path):
                initial_pos = os.path.getsize(dest_path)
                
            # Get remote file size
            head_req = requests.head(file_url, timeout=5)
            if head_req.status_code == 200 and 'Content-Length' in head_req.headers:
                remote_size = int(head_req.headers['Content-Length'])
                
                if initial_pos == remote_size:
                    print(f"Ficheiro {os.path.basename(dest_path)} já existe e está completo. A ignorar.")
                    return True
                elif initial_pos > remote_size:
                    # Local file is larger? Corrupted, start over.
                    print(f"Ficheiro local maior que o remoto. A reiniciar download...")
                    initial_pos = 0
                    file_mode = 'wb'
                elif initial_pos > 0:
                    headers['Range'] = f"bytes={initial_pos}-"
                    print(f"A retomar download de {os.path.basename(dest_path)}...")
            else:
                # Server doesn't support Content-Length or head request failed, start over
                initial_pos = 0
                file_mode = 'wb'

            response = requests.get(file_url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()
            
            # Content-length might not be accurate for chunked or ranged requests if not handled properly by the server
            # We use the initial remote_size we got from the HEAD request if available
            total_size = remote_size if 'remote_size' in locals() else int(response.headers.get('content-length', 0)) + initial_pos

            with open(dest_path, file_mode) as f:
                with tqdm(total=total_size, initial=initial_pos, unit='B', unit_scale=True, unit_divisor=1024, desc=os.path.basename(dest_path)) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"\nErro durante o download: {e}")
            if attempt < retries - 1:
                print(f"A tentar novamente em 3 segundos... (Tentativa {attempt + 2}/{retries})")
                time.sleep(3)
            else:
                print(f"Falha ao transferir {os.path.basename(dest_path)} após {retries} tentativas.")
                return False

def main():
    print("==================================================")
    print("      Sincronizador de Vídeos - SJCAM C100+       ")
    print("==================================================\n")
    
    wifi_ok = check_wifi()
    if not wifi_ok:
        print("A câmara precisa de estar ligada ao Wi-Fi para transferir os vídeos.")
        input("Pressione ENTER para tentar aceder mesmo assim ou feche a janela para cancelar...\n")
    
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Diretório local criado: {os.path.abspath(DOWNLOAD_DIR)}\n")

    videos = get_video_links(CAMERA_URL)
    
    if not videos:
        print("\nVerifique se o seu PC está ligado à rede Wi-Fi da câmara (geralmente começa por SJCAM_...).")
        return

    print("\nVídeos disponíveis para transferência:")
    for i, video in enumerate(videos, 1):
        filename = video.split('/')[-1]
        print(f"[{i}] {filename}")

    print("\nOpções:")
    print("[1] Transferir TODOS os vídeos")
    print("[2] Escolher vídeos específicos")
    print("[3] Sair")
    
    escolha = input("\nSelecione uma opção (1-3): ").strip()
    
    to_download = []
    
    if escolha == '1':
        to_download = videos
    elif escolha == '2':
        idxs = input("Introduza os números dos vídeos separados por espaço (ex: 1 3 5): ").strip().split()
        for idx in idxs:
            if idx.isdigit():
                i = int(idx) - 1
                if 0 <= i < len(videos):
                    to_download.append(videos[i])
    else:
        print("A sair...")
        return
        
    if not to_download:
        print("Nenhum vídeo válido foi selecionado.")
        return
        
    print(f"\nA iniciar transferência de {len(to_download)} vídeo(s)...")
    
    success_count = 0
    for video in to_download:
        # Se o link já for absoluto, urljoin lida com isso. Senão, anexa ao CAMERA_URL
        file_url = urljoin(CAMERA_URL, video)
        filename = video.split('/')[-1]
        dest_path = os.path.join(DOWNLOAD_DIR, filename)
        
        if download_file(file_url, dest_path):
            success_count += 1
            
    print(f"\nResumo: {success_count} de {len(to_download)} vídeos transferidos com sucesso!")
    print(f"Ficheiros guardados em: {os.path.abspath(DOWNLOAD_DIR)}")

if __name__ == "__main__":
    main()
