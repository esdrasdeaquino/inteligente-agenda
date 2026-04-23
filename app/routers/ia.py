from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.cliente_service import processar_mensagem_cliente
from app.services.admin_service import processar_mensagem_admin

router = APIRouter(prefix="/ia", tags=["Inteligência Artificial"])

class ChatPayload(BaseModel):
    empresa_id: int
    whatsapp_cliente: str
    mensagem: str
    historico: list = []

@router.post("/cliente")
async def chat_cliente(data: ChatPayload):
    try:
        # Chama o serviço que configuramos antes
        return processar_mensagem_cliente(
            empresa_id=data.empresa_id,
            whatsapp_cliente=data.whatsapp_cliente,
            mensagem=data.mensagem,
            historico=data.historico
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin")
async def chat_admin(data: ChatPayload):
    try:
        # No admin, o whatsapp_cliente é opcional, mas passamos por padrão
        return processar_mensagem_admin(
            empresa_id=data.empresa_id,
            mensagem=data.mensagem,
            historico=data.historico
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))