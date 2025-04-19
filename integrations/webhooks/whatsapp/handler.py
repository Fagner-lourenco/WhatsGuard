
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel
from integrations.whatsapp.client import send_text_v2
from core.fsm.state_manager import get_state, set_state
from core.pricing_engine.calculator import calcular_preco
from core.services.utils import create_service_request
from core.database.database import SessionLocal
import os, datetime, json

router=APIRouter(prefix="/webhook/whatsapp", tags=["Webhooks"])
SECRET=os.getenv("APIEVOLUTION_SECRET","")

class Msg(BaseModel):
    number:str
    text:str|None=None

@router.post("/")
async def receive(req:Request, bg:BackgroundTasks):
    if req.headers.get("x-api-key")!=SECRET:
        raise HTTPException(403,"invalid key")
    body=await req.json()
    # adapt to actual payload
    num=body.get("key",{}).get("remoteJid","").split("@")[0]
    msg_text=body.get("message",{}).get("conversation")
    event=Msg(number=num,text=msg_text)
    bg.add_task(process,event)
    return {"ok":True}

async def process(event:Msg):
    phone=event.number
    state=await get_state(phone)
    if not state:
        await send_text_v2(phone,"Olá! Digite 1 para solicitar segurança.")
        await set_state(phone,"START")
        return
    step=state["step"]
    if step=="START" and event.text=="1":
        await send_text_v2(phone,"Envie sua localização lat,lon:")
        await set_state(phone,"LOCATION")
        return
    if step=="LOCATION":
        try:
            lat,lon=map(float,event.text.split(","))
        except:
            await send_text_v2(phone,"Formato inválido, tente lat,lon")
            return
        price=calcular_preco(datetime.datetime.utcnow().hour,4.5,5)
        await set_state(phone,"CONFIRM",{"lat":lat,"lon":lon,"price":price})
        await send_text_v2(phone,f"Preço estimado R$ {price:.2f}. Confirmar? (sim/não)")
        return
    if step=="CONFIRM" and event.text.lower()=="sim":
        data=state["data"]
        db=SessionLocal()
        sid=create_service_request(db,0,f"{data['lat']},{data['lon']}",data["price"])
        db.close()
        await send_text_v2(phone,f"Solicitação #{sid} criada! Pague o link enviado.")
        await set_state(phone,"PAYMENT",{"service_id":sid})
        return
    await send_text_v2(phone,"Não entendi. Digite 1 para começar.")
