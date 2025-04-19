from fastapi import FastAPI

# já existente
from api.v1.services.routes import router as services_router

# >>> NOVO IMPORT <<<
from api.v1.professionals.routes import router as professionals_router

from integrations.webhooks.whatsapp.handler import router as whatsapp_router

from integrations.webhooks.mercadopago.handler import router as mp_router

app = FastAPI()

# já existente
app.include_router(services_router)

# >>> NOVA LINHA <<<
app.include_router(professionals_router)

app.include_router(whatsapp_router)

app.include_router(mp_router)
