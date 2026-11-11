# Qwen Alexa Skill Project

## Descrizione
Progetto per creare una skill Alexa che interroga un modello Qwen in esecuzione in locale.

## Struttura del progetto
- `server.py`: Proxy FastAPI che inoltra le richieste al modello Qwen locale (llama.cpp o Ollama)
- `app.py`: Backend della skill Alexa (riceve le richieste da Alexa e parla con Qwen)
- `requirements.txt`: Dipendenze Python

## Modello Qwen locale
Il modello `Qwen3-8B-Q4_K_M.gguf` è stato scaricato in:
```
/home/ray/llama_models/Qwen3-8B-Q4_K_M.gguf
```

## Setup

### 1. Avvia il server Qwen (llama.cpp)
```bash
/home/ray/llama.cpp/build/bin/llama-server \
  -m /home/ray/llama_models/Qwen3-8B-Q4_K_M.gguf \
  -ngl 99 \
  -c 8192 \
  --host 127.0.0.1 \
  --port 8080
```
In alternativa, usa Ollama (già in esecuzione con `qwen3.5:4b` sulla 11434):
```bash
QWEN_BACKEND=ollama python3 -m uvicorn server:app --port 8000
```

### 2. Installa le dipendenze Python
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Avvia il proxy Qwen
```bash
.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000
```

### 4. Avvia il backend Alexa
```bash
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8001
```

### 5. Esponi l'endpoint Alexa (es. con ngrok)
```bash
ngrok http 8001
```
Configura l'endpoint della skill Alexa puntando all'URL ngrok seguito da `/alexa`.

## Uso
- Invocation: "Chiedi a Qwen: [domanda]"
- Risposta: risposta generata da Qwen.

## Dipendenze
```txt
fastapi
uvicorn
httpx
```
