# Plano de Evolução: App SJCAM Downloader

## 1. Interface Gráfica (GUI)
- **Framework:** CustomTkinter (Python).
- **Motivo:** Cria uma aplicação de computador nativa, leve, moderna (com dark mode) sem depender do navegador.
- **Funcionalidades:** Botões intuitivos para as ações, barras de progresso visuais e uma interface limpa que esconde o terminal.

## 2. Automatização e Upload (A Abordagem "Simples e Eficaz")
- Em vez de usar a API do Google Drive (que exige tokens, expira a cada 7 dias e necessita de reautenticações constantes), vamos optar por uma organização local inteligente.
- O programa irá descarregar os vídeos da câmara e guardá-los localmente em pastas nomeadas por data (ex: `SJCAM_Para_Subir/2026-10-03/`).
- **Botão "Abrir Pasta":** Um botão na interface que abre a pasta correta diretamente no Windows, para que o utilizador possa simplesmente arrastar a pasta para o Google Drive no navegador de forma manual mas super rápida.

## 3. Função de Apagar (Limpeza Dupla)
- **Câmara:** Um botão/comando para enviar um pedido HTTP de exclusão para a SJCAM, limpando o cartão de memória remotamente e libertando espaço.
- **Computador (PC):** Um botão para apagar os ficheiros locais da máquina, **após** a edição ou upload para o Google Drive, garantindo que o disco não fica cheio.

## 4. Ordem de Execução
- A exclusão dos vídeos no PC só deve ocorrer **depois** da etapa de edição e criação de Reels (novo módulo).
