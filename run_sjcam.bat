@echo off
cd /d "C:\Users\Gabriel Martins\Desktop\Claude acesso\Documentos\Trabalho\sjcam_downloader"
call pip install -r requirements.txt >nul 2>&1
python app.py
pause
