import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="Qwen Alexa Proxy", version="1.0.0")

# Backend locale per Qwen.
# Default: Ollama (porta 11434) - più veloce per risposte vocali Alexa.
# Alternativa: llama.cpp (porta 8080) con Qwen3-8B-Q4_K_M.gguf (imposta QWEN_BACKEND=llama).
QWEN_BACKEND = os.getenv("QWEN_BACKEND", "ollama")
LLAMA_HOST = os.getenv("LLAMA_HOST", "http://127.0.0.1:8080")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")


class ChatRequest(BaseModel):
    query: str


@app.post("/api/v1/chat")
async def chat_endpoint(payload: ChatRequest):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query non puo' essere vuota")

    if QWEN_BACKEND == "ollama":
        return await _ollama_chat(query)
    return await _llama_chat(query)


async def _llama_chat(query: str):
    prompt = (
        "<|im_start|>system\n"
        "Sei un assistente vocale per Alexa. Rispondi in italiano in modo chiaro, "
        "breve e diretto. Massimo 1-2 frasi. Non ripetere la domanda.\n"
        "<|im_end|>\n"
        f"<|im_start|>user\n{query}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                f"{LLAMA_HOST}/completion",
                json={
                    "prompt": prompt,
                    "n_predict": 96,
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "stop": ["<|im_end|>", "<|im_start|>"],
                    "stream": False,
                },
            )
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502, detail=f"Impossibile contattare llama.cpp: {exc}"
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"llama.cpp ha risposto con errore: {exc.response.status_code}",
        )

    content = (data.get("content") or "").strip()
    return {"response": content or "Non ho ottenuto una risposta da Qwen."}


async def _ollama_chat(query: str):
    prompt = f"Rispondi in italiano in una frase breve e diretta.\nDomanda: {query}\nRisposta:"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "think": False,
                    "options": {"num_predict": 80, "temperature": 0.3},
                },
            )
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502, detail=f"Impossibile contattare Ollama: {exc}"
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama ha risposto con errore: {exc.response.status_code}",
        )

    response = (data.get("response") or "").strip()
    response = response.replace("**", "").strip()
    return {"response": response or "Nessuna risposta."}


@app.get("/health")
async def health():
    return {"status": "ok", "backend": QWEN_BACKEND}
