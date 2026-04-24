from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.cliente_service import processar_mensagem_cliente
from app.services.admin_service import processar_mensagem_admin
from app.database import supabase

router = APIRouter(prefix="/ia", tags=["Inteligência Artificial"])

# Modelo de dados esperado do Fiqon / Evolution API
class ChatPayload(BaseModel):
    instancia: str
    whatsapp_cliente: str
    mensagem: str
    historico: Optional[List] = []

@router.post("/cliente")
async def chat_cliente(data: ChatPayload):
    """
    Rota para clientes finais: focada em agendamento, preços e dúvidas.
    """
    try:
        # Busca a empresa vinculada à instância do WhatsApp
        res = supabase.table("empresas")\
            .select("id")\
            .eq("instancia", data.instancia)\
            .single()\
            .execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Instância de cliente não cadastrada.")

        empresa_id = int(res.data['id'])

        # Chama o motor de IA para clientes
        resultado = processar_mensagem_cliente(
            empresa_id=empresa_id,
            whatsapp_cliente=data.whatsapp_cliente,
            mensagem=data.mensagem
        )
        
        return resultado

    except Exception as e:
        print(f"Erro na Rota IA Cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin")
async def chat_admin(data: ChatPayload):
    """
    Rota para o Dono (IAgenda): focada em relatórios, bloqueios e gestão.
    """
    try:
        # Busca a empresa vinculada à instância
        res = supabase.table("empresas")\
            .select("id")\
            .eq("instancia", data.instancia)\
            .single()\
            .execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Instância de admin não encontrada.")

        empresa_id = res.data['id']

        # Chama o motor de IA para gestão (Admin)
        resultado = processar_mensagem_admin(
            empresa_id=empresa_id,
            mensagem=data.mensagem
        )
        
        return resultado

    except Exception as e:
        print(f"Erro na Rota IA Admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))