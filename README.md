# SJCAM C100+ Auto Downloader

Automação em Python e Batch para conectar, baixar e organizar automaticamente vídeos gravados na sua câmera de ação SJCAM C100+ via rede Wi-Fi local.

## O problema
Os aplicativos oficiais das câmeras de ação frequentemente são lentos e exigem muita intervenção manual para descarregar arquivos grandes.

## A Solução
Este script se conecta ao IP local da SJCAM, lista as mídias, faz o download dos vídeos novos, salva na pasta local `videos_sjcam` e (opcionalmente) limpa os arquivos baixados da câmera, tudo com um clique.

## Como rodar
1. Conecte o Wi-Fi do seu computador na rede gerada pela SJCAM C100+.
2. Instale as dependências: `pip install -r requirements.txt`.
3. Execute o script `run_sjcam.bat` (ou rode `python app.py` / `python sjcam_sync.py`).

## Tecnologias
- Python 3
- Requests (para scraping do diretório HTTP interno da câmera)
