from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.schemas import ServicoCreate, ProfissionalCreate, VincularServicosEmMassa
from datetime import date, datetime, time
from typing import Optional

router = APIRouter(prefix="/barbearia", tags=["Operação (Barbearia)"])

@router.post("/servicos")
def cadastrar_servico(dados: ServicoCreate):
    novo = {"empresa_id": dados.empresa_id, "nome": dados.nome, "preco": dados.preco, "duracao_minutos": dados.duracao}
    res = supabase.table("servicos").insert(novo).execute()
    return res.data

@router.post("/profissionais")
def cadastrar_profissional(dados: ProfissionalCreate):
    novo = {"empresa_id": dados.empresa_id, "nome": dados.nome, "especialidade": dados.especialidade}
    res = supabase.table("profissionais").insert(novo).execute()
    return res.data

@router.post("/vincular-servicos-massa")
def vincular_servicos_massa(dados: VincularServicosEmMassa):
    # Limpa vínculos antigos para não duplicar
    supabase.table("profissional_servicos").delete().eq("profissional_id", dados.profissional_id).execute()
    
    # Cria a lista para o Bulk Insert
    novos_vinculos = [{"profissional_id": dados.profissional_id, "servico_id": s_id} for s_id in dados.servicos_ids]
    
    if novos_vinculos:
        res = supabase.table("profissional_servicos").insert(novos_vinculos).execute()
        return {"status": "sucesso", "vinculos": len(res.data)}
    return {"status": "vazio"}

@router.get("/{empresa_id}/equipe-completa")
def listar_tudo(empresa_id: int):
    # Rota útil para o seu primo: traz profissionais e seus serviços vinculados
    profissionais = supabase.table("profissionais").select("*, profissional_servicos(servicos(*))").eq("empresa_id", empresa_id).execute()
    return profissionais.data

@router.get("/{empresa_id}/agendamentos")
def listar_agendamentos(empresa_id: int, data_especifica: Optional[date] = None):
    query = supabase.table("agendamentos")\
        .select("*, profissionais(nome), servicos(nome)")\
        .eq("empresa_id", empresa_id)

    if data_especifica:
        # Filtra do início do dia (00:00) até o fim do dia (23:59)
        inicio_dia = datetime.combine(data_especifica, time.min).isoformat()
        fim_dia = datetime.combine(data_especifica, time.max).isoformat()
        
        query = query.gte("data_hora", inicio_dia).lte("data_hora", fim_dia)
    else:
        # Se não passar data, traz tudo de "agora" em diante
        agora = datetime.now().isoformat()
        query = query.gte("data_hora", agora)

    res = query.order("data_hora", ascending=True).execute()
    return res.data