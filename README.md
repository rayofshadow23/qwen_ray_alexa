# Qwen Alexa Skill

Skill Alexa privata (solo per il tuo account) che inoltra le domande a un modello Qwen in esecuzione in locale e restituisce la risposta vocale.

## Struttura
- `server.py` — Proxy FastAPI verso il modello Qwen locale
- `app.py` — Backend Alexa (gestisce `LaunchRequest`, `IntentRequest`, `SessionEndedRequest`, endpoint `/alexa`)
- `requirements.txt` — Dipendenze Python
- `/home/ray/llama_models/Qwen3-8B-Q4_K_M.gguf` — Modello GGUF scaricato (uso alternativo con llama.cpp)

## Backend modello

Il proxy supporta due backend (configurabili via variabili d'ambiente):

| Backend | Default | Porta | Modello | Note |
|---|---|---|---|---|
| **Ollama** | sì (`QWEN_BACKEND=ollama`) | 11434 | `qwen3.5:4b` (`OLLAMA_MODEL`) | Più veloce per Alexa, usa `think: false` e risposte brevi |
| **llama.cpp** | no (`QWEN_BACKEND=llama`) | 8080 (`LLAMA_HOST`) | `Qwen3-8B-Q4_K_M.gguf` | Richiede `llama-server` attivo |

> Alexa richiede una risposta in pochi secondi: per questo il default è Ollama con prompt/timeout ottimizzati per risposte vocali brevi.

## Setup

### 1. Prerequisiti
- Python 3
- [Ollama](https://ollama.com/) con modello `qwen3.5:4b` **oppure** `llama-server` con GGUF
- `ngrok` (consigliato, HTTPS senza CAPTCHA) per esporre l'endpoint ad Alexa

### 2. Installa dipendenze
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Avvia i servizi
```bash
# (opzionale, solo se usi llama.cpp) llama-server
/home/ray/llama.cpp/build/bin/llama-server \
  -m /home/ray/llama_models/Qwen3-8B-Q4_K_M.gguf \
  -ngl 99 -c 8192 --host 127.0.0.1 --port 8080

# Proxy Qwen (porta 8000)
.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000

# Backend Alexa (porta 8001)
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8001

# Tunnel HTTPS verso la porta 8001
ngrok http 8001
```

Servizi necessari (default Ollama): Ollama su 11434, proxy su 8000, app Alexa su 8001, ngrok.

### 4. Configura la skill Alexa (privata)
1. [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) → **Crea skill** → nome es. `Qwen Ray`, locale `Italian`, modello **Custom**, hosting **Provision your own**, template **Start from Scratch**.
2. **Invocation**: `qwen ray` (almeno 2 parole).
3. **Interaction Model**: crea intent `AskQwenIntent` con slot `question` di tipo `AMAZON.SearchQuery` e frasi esempio:
   - `chiedi a qwen {question}`
   - `domanda a qwen {question}`
   - `qwen {question}`
   - `{question}`
4. **Salva modello** e **Crea modello** (Build).
5. **Endpoint → HTTPS**: `https://<tuo-ngrok>.ngrok.io/alexa` (SSL: *sub-domain with wildcard certificate from a CA*). Salva.
6. **Test**: abilita testing in Development e prova *"Alexa, apri qwen ray"* / *"chiedi a qwen ray qual è la capitale d'Italia"*.

> Non inviare la skill per la certificazione: resta in **Development** ed è utilizzabile solo dal tuo account/dispositivi associati.

## Test rapido (curl)
```bash
# Health
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8001/health

# Intent via endpoint pubblico
curl -s -X POST "https://<tuo-ngrok>.ngrok.io/alexa" \
  -H "Content-Type: application/json" \
  -d '{"version":"1.0","session":{"new":false,"sessionId":"t","application":{"applicationId":"t"},"attributes":{},"user":{"userId":"t"}},"request":{"type":"IntentRequest","requestId":"r2","timestamp":"2026-11-11T07:00:01Z","locale":"it-IT","intent":{"name":"AskQwenIntent","slots":{"question":{"name":"question","value":"Qual è la capitale d Italia?"}}}},"context":{"System":{"application":{"applicationId":"t"},"user":{"userId":"t"},"device":{"deviceId":"t","supportedInterfaces":{}}}}}'
```

## Note
- `localtunnel` mostra una pagina intermedia nel browser e può bloccare Alexa: preferire `ngrok`.
- Se cambia l'URL del tunnel, aggiorna l'endpoint nella console e salva.
- Dopo modifiche a invocation/intent, esegui sempre **Build Model**.
