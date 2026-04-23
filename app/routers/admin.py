from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase, verificar_admin
from app.schemas import BarbeariaCreate
from datetime import datetime, timedelta
from slugify import slugify
from app.services import ai_service


router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/cadastrar-barbearia")
def cadastrar_barbearia(dados: BarbeariaCreate, token: str = Depends(verificar_admin)):
    vencimento = (datetime.now() + timedelta(days=7)).date()
    slug_auto = slugify(dados.nome)
    
    nova_empresa = {
        "nome": dados.nome,
        "whatsapp_responsavel": dados.whatsapp_responsavel,
        "plano": dados.plano,
        "status": "trial",
        "slug": slug_auto,
        "data_vencimento": str(vencimento)
    }
    res = supabase.table("empresas").insert(nova_empresa).execute()
    return res.data

@router.get("/dashboard")
def dashboard(token: str = Depends(verificar_admin)):
    res = supabase.table("empresas").select("*").execute()
    empresas = res.data
    mrr = sum([24.90 if e['plano'] == 'essencial' else 49.90 for e in empresas if e['status'] == 'active'])
    return {"total_clientes": len(empresas), "mrr_estimado": f"R$ {mrr:.2f}"}

@router.patch("/barbearias/{empresa_id}/configurar-link")
def configurar_slug(empresa_id: int, slug: str, token: str = Depends(verificar_admin)):
    slug_limpo = slugify(slug)
    res = supabase.table("empresas").update({"slug": slug_limpo}).eq("id", empresa_id).execute()
    return {"status": "sucesso", "slug": slug_limpo}

@router.delete("/barbearias/{empresa_id}")
def deletar_barbearia(empresa_id: int, token: str = Depends(verificar_admin)):
    supabase.table("empresas").delete().eq("id", empresa_id).execute()
    return {"mensagem": "Removido com sucesso"}

@router.get("/ia-consultar")
def ia_consultar(pergunta: str, token: str = Depends(verificar_admin)):
    # Exemplo de pergunta: "Quantas barbearias temos no sistema agora?"
    #resposta = processar_pergunta_admin(pergunta)
    
    return ai_service.processar_pergunta_admin(pergunta)