# api/v1/mensagens/routes.py
from fastapi import APIRouter, HTTPException
from integrations.whatsapp.client import send_text_v2
from pydantic import BaseModel

router = APIRouter(prefix="/mensagens", tags=["Mensagens"])

class MensagemTextoInput(BaseModel):
    numero: str
    mensagem: str

@router.post("/texto")
async def enviar_texto(msg: MensagemTextoInput):
    sucesso = await send_text_v2(msg.numero, msg.mensagem)
    if not sucesso:
        raise HTTPException(status_code=400, detail="Erro ao enviar mensagem")
    return {"msg": "Mensagem enviada com sucesso"}
