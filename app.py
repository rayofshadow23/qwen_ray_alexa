from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import httpx
import uuid

app = FastAPI(title="Qwen Alexa Skill", version="1.0.0")

QWEN_SERVER = "http://127.0.0.1:8000"


class AlexaRequest(BaseModel):
    version: str
    session: dict
    request: dict
    context: dict = {}


def build_response(text: str, end_session: bool = True) -> dict:
    return {
        "version": "1.0",
        "sessionAttributes": {},
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text,
            },
            "shouldEndSession": end_session,
        },
    }


def build_error_response() -> dict:
    return build_response(
        "Mi dispiace, non sono riuscito a contattare Qwen. Riprova piu' tardi.",
        end_session=True,
    )


@app.post("/alexa")
async def alexa_handler(request: Request):
    body = await request.json()

    request_type = body.get("request", {}).get("type")

    # LaunchRequest: skill avviata senza invocation name specifico
    if request_type == "LaunchRequest":
        return build_response(
            "Ciao! Sono Qwen. Di cosa vuoi parlare?",
            end_session=False,
        )

    # SessionEndedRequest: sessione terminata
    if request_type == "SessionEndedRequest":
        return build_response("A presto!", end_session=True)

    # IntentRequest: comando dell'utente
    if request_type == "IntentRequest":
        intent = body.get("request", {}).get("intent", {})
        intent_name = intent.get("name", "")
        slots = intent.get("slots", {}) or {}

        # Estrai la domanda dallo slot "question"
        question = None
        question_slot = slots.get("question") or {}
        if question_slot.get("value"):
            question = question_slot["value"]

        # Fallback: prova a leggere da altri slot possibili
        if not question:
            for slot_name, slot_val in slots.items():
                if isinstance(slot_val, dict) and slot_val.get("value"):
                    question = slot_val["value"]
                    break

        # Fallback per intent generici tipo "QwenIntent" senza slot named question
        if not question and intent_name in ("AskQwenIntent", "QwenIntent"):
            # qualche skill invia il testo in "query"
            question = intent.get("slots", {}).get("query", {}).get("value")

        if not question:
            return build_response(
                "Non ho capito la domanda. Dimmi: Chiedi a Qwen, seguito dalla tua domanda.",
                end_session=False,
            )

        # Inoltra la domanda al server Qwen locale (Alexa richiede risposta entro ~8s)
        try:
            async with httpx.AsyncClient(timeout=7.5) as client:
                resp = await client.post(
                    f"{QWEN_SERVER}/api/v1/chat",
                    json={"query": question},
                )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("response", "").strip() or "Non ho ottenuto una risposta da Qwen."
        except Exception:
            return build_error_response()

        # Alexa ha limiti sulla lunghezza del testo; tronchiamo per sicurezza
        if len(answer) > 700:
            answer = answer[:700].rsplit(" ", 1)[0] + "."
        return build_response(answer, end_session=True)

    # Richiesta sconosciuta
    raise HTTPException(status_code=400, detail="Tipo di richiesta Alexa non supportato")


@app.get("/health")
async def health():
    return {"status": "ok"}
