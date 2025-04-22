import os, httpx, json

DOMAIN   = os.getenv("API_DOMAIN", "").rstrip("/")
INSTANCE = os.getenv("INSTANCE_NAME")
API_KEY  = os.getenv("WHATSAPP_APIKEY")

HEADERS = {
    "apikey": API_KEY,
    "Content-Type": "application/json",
}


# ------------------ baixo‑nível ------------------ #
async def _post(route: str, payload: dict):
    url = f"{DOMAIN}{route}/{INSTANCE}"
    # log de saída
    print(f"[WA‑SEND] → {url}  {json.dumps(payload, ensure_ascii=False)[:200]}")

    async with httpx.AsyncClient(timeout=10) as cli:
        try:
            r = await cli.post(url, json=payload, headers=HEADERS)
            print(f"[WA‑SEND] ← {r.status_code} {r.text[:120]}")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            print(f"[WA‑ERR] {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"[WA‑ERR] {e}")
    return None


# ------------------ helpers de envio ------------------ #
async def send_text_v2(number: str, text: str):
    return await _post("/message/sendText", {
        "number": number,
        "text":   text 
    })


async def send_location_v2(number: str, lat: float, lon: float,
                           name: str = "", address: str = ""):
    return await _post("/message/sendLocation", {
        "number": number,
        "locationMessage": {
            "latitude":  lat,
            "longitude": lon,
            "name":      name,
            "address":   address,
        }
    })


async def send_buttons_v2(number: str, text: str, buttons: list[dict]):
    """
    buttons = [
        {"buttonId": "confirmar", "buttonText": {"displayText": "✅ Sim"}, "type": 1},
        {"buttonId": "cancelar",  "buttonText": {"displayText": "❌ Não"}, "type": 1},
    ]
    """
    return await _post("/message/sendButtons", {
        "number": number,
        "buttonMessage": {
            "text":    text,
            "buttons": buttons
        }
    })
