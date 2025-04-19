import os, httpx, asyncio

DOMAIN = os.getenv("API_DOMAIN", "").rstrip("/")
INSTANCE = os.getenv("INSTANCE_NAME")
API_KEY = os.getenv("WHATSAPP_APIKEY")

HEADERS = { "apikey": API_KEY, "Content-Type": "application/json" }

async def _post(route: str, payload: dict):
    url = f"{DOMAIN}{route}/{INSTANCE}"
    async with httpx.AsyncClient(timeout=10) as cli:
        r = await cli.post(url, json=payload, headers=HEADERS)
        if r.status_code == 201:
            return True
        print(f"[EvolutionAPI] error {r.status_code}: {r.text}")
        return False

async def send_text_v2(number: str, text: str):
    return await _post("/message/sendText", {
        "number": number,
        "textMessage": {
            "text": text
        }
    })

async def send_location_v2(number: str, lat: float, lon: float, name: str, address: str):
    return await _post("/message/sendLocation", {
        "number": number,
        "locationMessage": {
            "latitude": lat,
            "longitude": lon,
            "name": name,
            "address": address
        }
    })
