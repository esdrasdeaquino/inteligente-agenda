from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.schemas import AgendamentoCreate
from datetime import datetime, time, date

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"])

@router.post("/")
def criar_agendamento(dados: AgendamentoCreate):
    # Aqui o sistema salva a reserva de horário
    novo = {
        "empresa_id": dados.empresa_id,
        "profissional_id": dados.profissional_id,
        "servico_id": dados.servico_id,
        "nome_cliente": dados.nome_cliente,
        "whatsapp_cliente": dados.whatsapp_cliente,
        "data_hora": dados.data_hora.isoformat(),
        "status": "pendente"
    }
    res = supabase.table("agendamentos").insert(novo).execute()
    return {"status": "agendado", "detalhes": res.data}

@router.get("/profissional/{profissional_id}/hoje")
def listar_agenda_barbeiro_hoje(profissional_id: int):
    # 1. Pegamos a data de hoje
    hoje = date.today()
    
    # 2. Definimos o início (00:00:00) e o fim do dia (23:59:59)
    inicio_dia = datetime.combine(hoje, time.min).isoformat()
    fim_dia = datetime.combine(hoje, time.max).isoformat()
    
    # 3. Consultamos o banco filtrando pelo ID e pelo intervalo de tempo
    res = supabase.table("agendamentos")\
        .select("*, servicos(nome, preco)")\
        .eq("profissional_id", profissional_id)\
        .gte("data_hora", inicio_dia)\
        .lte("data_hora", fim_dia)\
        .order("data_hora", ascending=True)\
        .execute()
        
    return res.data
