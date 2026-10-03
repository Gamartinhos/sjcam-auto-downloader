import customtkinter as ctk
import os
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import subprocess
import tkinter.messagebox as messagebox
import shutil
import time

# Configurações globais
CAMERA_URL = "http://192.168.1.254/DCIM/Movie/"
BASE_DOWNLOAD_DIR = "./SJCAM_Para_Subir/"
EXPECTED_WIFI_PREFIX = "C100+"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SJCAMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Estúdio SJCAM C100+")
        self.geometry("650x550")
        self.resizable(False, False)
        
        # UI Layout
        self.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Estúdio SJCAM C100+", font=ctk.CTkFont(size=26, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 5))
        
        self.status_label = ctk.CTkLabel(self, text="A aguardar ação...", font=ctk.CTkFont(size=14), text_color="gray")
        self.status_label.grid(row=1, column=0, padx=20, pady=5)
        
        # Frame de botões principais
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.btn_download = ctk.CTkButton(self.btn_frame, text="⬇️ Descarregar Vídeos (Câmara -> PC)", command=self.start_download, height=45, font=ctk.CTkFont(weight="bold"))
        self.btn_download.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_open_folder = ctk.CTkButton(self.btn_frame, text="📂 Abrir Pasta (Arraste para o Drive)", command=self.open_folder, height=45, fg_color="#28a745", hover_color="#218838", font=ctk.CTkFont(weight="bold"))
        self.btn_open_folder.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Frame de Limpeza
        self.clean_frame = ctk.CTkFrame(self)
        self.clean_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.clean_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.btn_clean_cam = ctk.CTkButton(self.clean_frame, text="🗑️ Limpar Câmara", command=self.clean_camera, fg_color="#dc3545", hover_color="#c82333", height=40)
        self.btn_clean_cam.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_clean_pc = ctk.CTkButton(self.clean_frame, text="🗑️ Apagar Ficheiros Locais (PC)", command=self.clean_pc, fg_color="#dc3545", hover_color="#c82333", height=40)
        self.btn_clean_pc.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        self.progress_bar.set(0)
        
        # Logs
        self.log_textbox = ctk.CTkTextbox(self, height=180, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.log("▶ Bem-vindo ao Estúdio SJCAM. Conecte-se ao Wi-Fi da câmara para começar.")
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.update_idletasks()
        
    def check_wifi(self):
        self.log("A verificar ligação Wi-Fi...")
        try:
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if "SSID" in line and "BSSID" not in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        ssid = parts[1].strip()
                        if ssid.startswith(EXPECTED_WIFI_PREFIX) or ssid == "C100+_GC140a028a71bb":
                            self.log(f"Ligado à rede da câmara: {ssid}")
                            return True
                        else:
                            self.log(f"Aviso: Ligado à rede '{ssid}'. Se não for a câmara, isto falhará.")
                            return False
            self.log("Não foi possível detetar o SSID atual.")
            return False
        except Exception as e:
            self.log(f"Erro ao verificar Wi-Fi: {e}")
            return False

    def get_today_dir(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        dir_path = os.path.join(BASE_DOWNLOAD_DIR, today_str)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def start_download(self):
        self.btn_download.configure(state="disabled")
        threading.Thread(target=self.download_process, daemon=True).start()
        
    def download_process(self):
        if not self.check_wifi():
            self.log("Certifique-se de que a câmara está ligada e emparelhada por Wi-Fi.")
            
        self.status_label.configure(text="A contactar a câmara...", text_color="orange")
        
        try:
            response = requests.get(CAMERA_URL, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            
            videos = []
            for link in links:
                href = link.get('href')
                if href and href.upper().endswith('.MP4'):
                    videos.append(href)
                    
            videos = list(set(videos))
            self.log(f"Encontrados {len(videos)} vídeos na câmara.")
            self.progress_bar.set(0)
            
            if not videos:
                self.status_label.configure(text="Nenhum vídeo encontrado.", text_color="white")
                self.btn_download.configure(state="normal")
                return
                
            dest_dir = self.get_today_dir()
            self.log(f"Destino: {os.path.abspath(dest_dir)}")
            
            for i, video in enumerate(videos):
                self.status_label.configure(text=f"A transferir vídeo {i+1} de {len(videos)}...")
                file_url = urljoin(CAMERA_URL, video)
                filename = video.split('/')[-1]
                dest_path = os.path.join(dest_dir, filename)
                
                success = self.download_single_file(file_url, dest_path, filename)
                if not success:
                    self.log("Transferência abortada devido a erros de rede.")
                    break
                self.progress_bar.set((i + 1) / len(videos))
                
            self.status_label.configure(text="Transferência Concluída!", text_color="#28a745")
            self.log("Todos os vídeos processados.")
            
        except Exception as e:
            self.log(f"Erro crítico ao contactar a câmara: {e}")
            self.status_label.configure(text="Erro de Ligação.", text_color="red")
            
        self.btn_download.configure(state="normal")
        
    def download_single_file(self, file_url, dest_path, filename, retries=5):
        for attempt in range(retries):
            try:
                headers = {}
                file_mode = 'ab'
                initial_pos = 0
                
                if os.path.exists(dest_path):
                    initial_pos = os.path.getsize(dest_path)
                    
                head_req = requests.head(file_url, timeout=5)
                remote_size = int(head_req.headers.get('Content-Length', 0))
                
                if remote_size > 0 and initial_pos == remote_size:
                    self.log(f"✓ Já existe: {filename}")
                    return True
                elif remote_size > 0 and initial_pos > remote_size:
                    initial_pos = 0
                    file_mode = 'wb'
                elif initial_pos > 0:
                    headers['Range'] = f"bytes={initial_pos}-"
                    
                self.log(f"A transferir {filename}...")
                
                response = requests.get(file_url, headers=headers, stream=True, timeout=10)
                response.raise_for_status()
                
                with open(dest_path, file_mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                self.log(f"✓ Concluído: {filename}")
                return True
                
            except requests.exceptions.RequestException as e:
                self.log(f"Erro ({attempt+1}/{retries}) no {filename} (Time-out/Queda)")
                if attempt < retries - 1:
                    time.sleep(3)
                else:
                    self.log(f"❌ Falha persistente ao transferir {filename}.")
                    return False
                    
    def open_folder(self):
        try:
            path = os.path.abspath(BASE_DOWNLOAD_DIR)
            if not os.path.exists(path):
                os.makedirs(path)
            os.startfile(path)
            self.log("Pasta aberta no Explorador de Ficheiros.")
        except Exception as e:
            self.log(f"Erro ao abrir pasta: {e}")
            
    def clean_camera(self):
        resposta = messagebox.askyesno("Confirmar Limpeza da Câmara", "Tem a certeza que deseja APAGAR TODOS os vídeos do cartão de memória da câmara?\n\nIsto não pode ser desfeito.")
        if resposta:
            self.btn_clean_cam.configure(state="disabled")
            threading.Thread(target=self.clean_camera_process, daemon=True).start()
        
    def clean_camera_process(self):
        if not self.check_wifi():
            self.log("Erro: Câmara não conectada.")
            self.btn_clean_cam.configure(state="normal")
            return
            
        self.status_label.configure(text="A limpar câmara...", text_color="orange")
        self.log("A obter lista de ficheiros na câmara para exclusão...")
        try:
            response = requests.get(CAMERA_URL, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            
            videos = list(set([link.get('href') for link in links if link.get('href') and link.get('href').upper().endswith('.MP4')]))
            
            self.progress_bar.set(0)
            count = 0
            for i, video in enumerate(videos):
                url = urljoin(CAMERA_URL, video)
                filename = video.split('/')[-1]
                self.log(f"A apagar da câmara: {filename}")
                resp = requests.delete(url, timeout=5)
                if resp.status_code == 200:
                    count += 1
                self.progress_bar.set((i + 1) / len(videos))
                time.sleep(0.2)
                
            self.log(f"Limpeza concluída! {count} ficheiros removidos.")
            self.status_label.configure(text="Câmara limpa!", text_color="#28a745")
        except Exception as e:
            self.log(f"Erro ao limpar câmara: {e}")
            self.status_label.configure(text="Erro ao limpar", text_color="red")
            
        self.btn_clean_cam.configure(state="normal")
        
    def clean_pc(self):
        path = os.path.abspath(BASE_DOWNLOAD_DIR)
        if not os.path.exists(path):
            self.log("Não há ficheiros locais para apagar.")
            return
            
        resposta = messagebox.askyesno("Confirmar Limpeza Local", "Tem a certeza que deseja APAGAR TODOS os vídeos já transferidos para o seu PC?\n\nCertifique-se que já arrastou a pasta para o Google Drive primeiro.")
        
        if resposta:
            try:
                shutil.rmtree(path)
                os.makedirs(path)
                self.log("Ficheiros locais apagados do PC. Espaço libertado com sucesso!")
            except Exception as e:
                self.log(f"Erro ao apagar ficheiros locais: {e}")

if __name__ == "__main__":
    app = SJCAMApp()
    app.mainloop()
