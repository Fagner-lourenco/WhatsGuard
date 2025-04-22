from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from integrations.whatsapp.client import send_text_v2
from core.fsm.state_manager import get_state, set_state
from core.pricing_engine.calculator import calcular_preco
from pathlib import Path
import datetime, json, httpx, requests
import re

router = APIRouter(prefix="/webhook/whatsapp", tags=["Webhooks"])

UPLOAD_DIR = Path("uploads/documentos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Msg(BaseModel):
    number: str
    text: str | None = None
    lat: float | None = None
    lon: float | None = None
    image_url: str | None = None
    image_caption: str | None = None

def _client_number(payload: dict) -> str:
    return payload.get("data", {}).get("key", {}).get("remoteJid", "").split("@")[0]

def extract_msg(payload: dict) -> Msg | None:
    data = payload.get("data", {})
    key = data.get("key", {})
    if key.get("fromMe"):
        return None
    number = _client_number(payload)
    m = data.get("message", {})

    if "conversation" in m:
        return Msg(number=number, text=m["conversation"].strip().lower())
    if "buttonsResponseMessage" in m:
        return Msg(number=number, text=m["buttonsResponseMessage"]["selectedButtonId"].lower())
    if "imageMessage" in m:
        media_url = m["imageMessage"].get("url")
        caption = m["imageMessage"].get("caption")
        return Msg(number=number, text=caption.strip().lower() if caption else None, image_url=media_url, image_caption=caption)
    if "locationMessage" in m:
        loc = m["locationMessage"]
        try:
            lat = float(loc.get("degreesLatitude"))
            lon = float(loc.get("degreesLongitude"))
        except (TypeError, ValueError):
            lat = lon = None
        return Msg(number=number, lat=lat, lon=lon)

    return Msg(number=number)

@router.post("/")
async def receive(req: Request, bg: BackgroundTasks):
    payload = await req.json()
    print("[Webhook] 🔔", json.dumps(payload)[:200], "...")
    msg = extract_msg(payload)
    if not msg:
        return {"ok": True}
    bg.add_task(process, msg)
    return {"ok": True}

async def process(msg: Msg):
    phone = msg.number
    state = await get_state(phone) or {"step": "START", "data": {}}
    step = state["step"]
    data = state.get("data", {})

    print(f"[FSM] phone='{phone}' step='{step}' msg.text='{msg.text}'")

    if msg.text == "cancelar":
        await send_text_v2(phone, "❌ Pedido cancelado. Digite *começar* para iniciar novamente.")
        await set_state(phone, "START")
        return

    if step == "START" or msg.text == "começar":
        await send_text_v2(phone, "👋 Olá! Qual seu nome completo?")
        await set_state(phone, "NOME")
        return

    if step == "NOME":
        data["nome"] = msg.text
        async with httpx.AsyncClient() as client:
            # Verifica se cliente já existe
            r_check = await client.get(f"http://localhost:8000/clientes/?telefone={phone}")
            if r_check.status_code == 200 and r_check.json():
                client_id = r_check.json()[0]["id"]
            else:
                r_create = await client.post("http://localhost:8000/clientes/", json={
                    "nome": data["nome"],
                    "telefone": phone,
                    "email": f"{phone}@fake.com"
                })
                if r_create.status_code == 200:
                    client_id = r_create.json()["id"]
                else:
                    await send_text_v2(phone, "❌ Erro ao registrar cliente. Tente novamente.")
                    await set_state(phone, "START")
                    return
            data["client_id"] = client_id
        await send_text_v2(phone, "Digite o tipo de segurança desejado:\n- padrão\n- evento\n- guarda-costas")
        await set_state(phone, "TIPO_SERVICO", data)
        return


    if step == "TIPO_SERVICO":
        data["tipo"] = msg.text
        await send_text_v2(phone, "O serviço será:\n- agora\n- agendar\n\nDigite uma das opções.")
        await set_state(phone, "AGENDAMENTO", data)
        return

    if step == "AGENDAMENTO":
        data["agendamento"] = msg.text
        await send_text_v2(phone, "Informe a data e hora do serviço. Ex: 22/04 às 20h")
        await set_state(phone, "DATA_HORA", data)
        return

    if step == "DATA_HORA":
        data["data_hora"] = msg.text
        await send_text_v2(phone, "📍 Envie sua localização ou digite o endereço do serviço.")
        await set_state(phone, "ENDERECO", data)
        return

    if step == "ENDERECO":
        data["endereco"] = msg.text or f"{msg.lat},{msg.lon}"
        await send_text_v2(phone, "Quantos agentes deseja contratar?")
        await set_state(phone, "QUANTIDADE", data)
        return

    if step == "QUANTIDADE":
        data["quantidade"] = msg.text
        await send_text_v2(phone, "Qual a duração do serviço (mínimo 1h)?")
        await set_state(phone, "DURACAO", data)
        return

    if step == "DURACAO":
        data["duracao"] = msg.text
        await send_text_v2(phone, "Digite o traje desejado para os agentes:\n- tatico\n- social\n- padrao")
        await set_state(phone, "TRAJE", data)
        return

    if step == "TRAJE":
        data["traje"] = msg.text
        await send_text_v2(phone, "Digite os equipamentos desejados separados por vírgula:\nEx: talkie, detector")
        await set_state(phone, "EQUIPAMENTOS", data)
        return

    if step == "EQUIPAMENTOS":
        data["equipamentos"] = [e.strip() for e in msg.text.split(",") if e.strip()]
        preco = calcular_preco(datetime.datetime.utcnow().hour, float(data["quantidade"] or 1), float(data["duracao"] or 1))
        data["preco"] = preco

        # Buscar client_id por telefone
        async with httpx.AsyncClient() as client:
            r_client = await client.get(f"http://localhost:8000/clientes/?telefone={phone}")
            if r_client.status_code == 200 and r_client.json():
                client_id = r_client.json()[0]["id"]
            else:
                await send_text_v2(phone, "❌ Não foi possível encontrar seu cadastro. Digite *começar* para reiniciar.")
                await set_state(phone, "START")
                return

            # Criar solicitação
            r_solic = await client.post("http://localhost:8000/solicitacoes/", json={
                "client_id": client_id,
                "location": data["endereco"],
                "scheduled_datetime": datetime.datetime.utcnow().isoformat(),
                "service_type": data["tipo"],
                "agent_count": int(data["quantidade"]),
                "duration_hours": int(data["duracao"]),
                "attire": data["traje"],
                "equipments": data["equipamentos"]
            })

            if r_solic.status_code == 200:
                resp = r_solic.json()
                data["solicitacao_id"] = resp["id"]
            else:
                await send_text_v2(phone, "❌ Erro ao criar solicitação. Tente novamente mais tarde.")
                await set_state(phone, "START")
                return

        resumo = f"**Resumo da Missão:**\n\n👥 *{data['quantidade']} agentes* | ⏱️ *{data['duracao']}h* | 🧥 *{data['traje']}*\n🔧 *{', '.join(data['equipamentos'])}*\n📍 *{data['endereco']}*\n📅 *{data['data_hora']}*\n💰 *R$ {preco:.2f}*\n\nDeseja confirmar o pagamento via PIX?"
        await send_text_v2(phone, resumo + "\n\nResponda com *sim* para confirmar ou *não* para cancelar.")
        await set_state(phone, "PAGAMENTO", data)
        return


    if step == "PAGAMENTO":
        if msg.text == "sim":
            await send_text_v2(phone, "Aqui está o QR Code PIX para pagamento: [LINK FICTÍCIO]")
            await set_state(phone, "AGUARDANDO_PAGAMENTO", data)
        else:
            await send_text_v2(phone, "Pagamento não confirmado. Pedido cancelado.")
            await set_state(phone, "START")
        return


    if step == "AGUARDANDO_PAGAMENTO":
        # Apenas confirmar pagamento e seguir para a próxima etapa
        if not data.get("solicitacao_id"):
            await send_text_v2(phone, "❌ Erro interno: solicitação não encontrada. Digite *começar* para reiniciar.")
            await set_state(phone, "START")
            return

        await send_text_v2(phone, "✅ Pagamento confirmado! Estamos procurando um profissional disponível para você...")
        await set_state(phone, "DISTRIBUICAO", data)
        return


    if step == "DISTRIBUICAO":
        solicitacao_id = data.get("solicitacao_id")
        if not solicitacao_id:
            await send_text_v2(phone, "❌ Erro interno: ID da solicitação ausente.")
            await set_state(phone, "START")
            return

        async with httpx.AsyncClient() as client:
            # Busca todos os profissionais cadastrados
            r_prof = await client.get("http://localhost:8000/profissionais/")
            if r_prof.status_code != 200:
                await send_text_v2(phone, "⚠️ Erro ao buscar profissionais. Tente novamente.")
                return

            profissionais = r_prof.json()
            online = [p for p in profissionais if p.get("status") == "ONLINE"]

            if not online:
                await send_text_v2(phone, "⚠️ Nenhum profissional disponível no momento. Tente novamente mais tarde.")
                return

            profissional = online[0]  # simples: pega o primeiro disponível
            prof_id = profissional["id"]

            # Atribui o profissional à solicitação
            r_match = await client.patch(f"http://localhost:8000/solicitacoes/{solicitacao_id}/aceitar", json={
                "profissional_id": prof_id
            })

            if r_match.status_code == 200:
                await send_text_v2(phone, f"👮 *{profissional['nome']}* aceitou sua missão e está a caminho! Em breve ele enviará uma confirmação de chegada.")
                await set_state(phone, "AGUARDANDO_CHEGADA", data)
            else:
                print(f"[ERRO] PATCH /solicitacoes/{solicitacao_id}/aceitar => {r_match.status_code}: {r_match.text}")
                await send_text_v2(phone, "❌ Erro ao atribuir profissional. Tente novamente.")
                await set_state(phone, "START")
        return




    if step == "AGUARDANDO_CHEGADA" and msg.text == "cheguei":
        async with httpx.AsyncClient() as client:
            try:
                await client.patch(f"http://localhost:8000/solicitacoes/{data['solicitacao_id']}/confirmar_chegada")
            except Exception as e:
                print(f"[ERRO CHEGADA] {e}")
        await send_text_v2(phone, "🔔 O profissional chegou ao local e está iniciando o serviço.")
        await set_state(phone, "EM_ANDAMENTO", data)
        return

    if step == "EM_ANDAMENTO" and msg.text == "finalizar":
        async with httpx.AsyncClient() as client:
            try:
                await client.patch(f"http://localhost:8000/solicitacoes/{data['solicitacao_id']}/finalizar")
            except Exception as e:
                print(f"[ERRO FINALIZAR] {e}")
        await send_text_v2(phone, "✅ Serviço finalizado! Por favor, avalie o atendimento de 0 a 5, seguido de um comentário.\nEx: *5 Profissional educado e pontual*")
        await set_state(phone, "AVALIACAO", data)
        return
    
    if step == "AVALIACAO":
        match = re.match(r"(\d(?:\.0)?|\d)(?:\s*[-:]?\s*)(.*)", msg.text or "")
        if not match:
            await send_text_v2(phone, "❌ Envie a nota de 0 a 5 seguida de um comentário. Ex: *5 Excelente profissional!*")
            return
        nota = float(match.group(1))
        if nota < 0 or nota > 5:
            await send_text_v2(phone, "❌ Nota inválida. Envie um número entre 0 e 5.")
            return
        comentario = match.group(2).strip()
        async with httpx.AsyncClient() as client:
            try:
                await client.post("http://localhost:8000/avaliacoes/", json={
                    "solicitacao_id": data.get("solicitacao_id"),
                    "nota": nota,
                    "comentario": comentario
                })
            except Exception as e:
                print(f"[ERRO AVALIACAO] {e}")
        await send_text_v2(phone, "🙏 Obrigado pela avaliação! Até a próxima.")
        await set_state(phone, "FIM", {})
        return

    if step == "FIM":
        await send_text_v2(phone, "👋 Atendimento finalizado. Digite *começar* para novo pedido.")
        return

    if msg.text == "registrar":
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8000/profissionais/", json={
                "name": "Profissional Temporário",
                "cpf": "00000000000",
                "phone": phone
            })
        await send_text_v2(phone, "📸 Envie agora a foto da sua *CNH* (com legenda 'cnh').")
        await set_state(phone, "DOC_CNH")
        return

    if step == "DOC_CNH" and msg.image_url and msg.text == "cnh":
        try:
            r = requests.get(msg.image_url)
            filename = f"prof_{phone[-4:]}_cnh.jpg"
            path = UPLOAD_DIR / filename
            with open(path, "wb") as f:
                f.write(r.content)
            async with httpx.AsyncClient() as client:
                await client.post(f"http://localhost:8000/profissionais/documentos", files={
                    "arquivo": (filename, open(path, "rb"), "image/jpeg")
                }, data={"tipo": "CNH", "telefone": phone})
            await send_text_v2(phone, "✅ CNH recebida. Digite *online* quando estiver disponível para atendimento.")
            await set_state(phone, "APROVADO")
        except Exception as e:
            print(f"[ERRO CNH] {e}")
            await send_text_v2(phone, "❌ Erro ao processar a imagem. Tente novamente.")
        return

    if step == "APROVADO" and msg.text == "online":
        async with httpx.AsyncClient() as client:
            await client.post(f"http://localhost:8000/profissionais/checkin", json={"telefone": phone})
        await send_text_v2(phone, "🔔 Você está online e disponível para atender.")
        await set_state(phone, "ONLINE")
        return

    if step == "ONLINE" and msg.text == "aceitar":
        await send_text_v2(phone, "👍 Serviço aceito. Boa viagem!")
        await set_state(phone, "IN_PROGRESS")
        return

    if step == "IN_PROGRESS" and msg.text == "finalizar":
        await send_text_v2(phone, "✅ Atendimento finalizado. Digite *online* para aceitar novos chamados ou *offline* para sair.")
        await set_state(phone, "DISPONIVEL")
        return

    if step in {"ONLINE", "DISPONIVEL"} and msg.text == "offline":
        async with httpx.AsyncClient() as client:
            await client.post(f"http://localhost:8000/profissionais/checkout", json={"telefone": phone})
        await send_text_v2(phone, "✋ Até logo. Você está offline.")
        await set_state(phone, "APROVADO")
        return

    await send_text_v2(phone, "👍 Recebido! Em breve teremos mais etapas automatizadas. 😉")
