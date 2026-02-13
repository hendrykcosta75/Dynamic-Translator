# Dynamic Translator

Um tradutor automático que monitora o texto selecionado (em qualquer aplicativo) e exibe um popup com a tradução para português.

## Funcionalidades

- **Tradução Instantânea**: Selecione texto com o mouse para ver a tradução.
- **Universal**: Funciona em navegadores, editores de texto, PDFs, etc.
- **Discreto**: Ícone na bandeja do sistema para controle.
- **Popup Flutuante**: A tradução aparece perto do cursor e desaparece automaticamente.

## Instalação

1. Certifique-se de ter o Python instalado.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. renomeie o arquivo .env.example para .env

## Como Usar

1. Execute o aplicativo:
   ```bash
   python src/main.py
   ```
2. Selecione qualquer texto em qualquer janela usando o mouse.
3. Um pequeno popup aparecerá com a tradução.
4. Para sair, clique com o botão direito no ícone da bandeja do sistema e escolha "Quit".

## Notas

- O aplicativo simula um comando `Ctrl+C` para capturar o texto selecionado. Isso substituirá o conteúdo atual da sua área de transferência.

## Tecnologias

- **Python**
- **tkinter** (GUI)
- **pynput** (Monitoramento de mouse/teclado)
- **deep-translator** (Serviço de tradução)
- **pystray** (Ícone da bandeja)
