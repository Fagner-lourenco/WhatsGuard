from fastapi import FastAPI

# já existente
from api.v1.services.routes import router as services_router

# >>> NOVO IMPORT <<<
from api.v1.professionals.routes import router as professionals_router

from integrations.webhooks.whatsapp.handler import router as whatsapp_router

from integrations.webhooks.mercadopago.handler import router as mp_router
from api.v1.clients.routes import router as clients_router
from api.v1.evaluations.routes import router as evaluations_router
from api.v1.mensagens.routes import router as mensagens_router

app = FastAPI(
    title="WhatsGuard API",
    version="1.0.0",
    description="API para gerenciamento de segurança privada via WhatsApp."
)

# já existente
app.include_router(services_router)

# >>> NOVA LINHA <<<
app.include_router(professionals_router)

app.include_router(whatsapp_router)

app.include_router(mp_router)

app.include_router(clients_router)

app.include_router(evaluations_router)
app.include_router(mensagens_router)
