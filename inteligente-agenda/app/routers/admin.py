from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase, verificar_admin
from pydantic import BaseModel
from typing import List, Optional
from slugify import slugify
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])

# --- SCHEMAS (Modelos para Criação) ---

class EmpresaCreate(BaseModel):
    nome: str
    whatsapp_responsavel: str
    plano: str = "essencial"

class UsuarioCreate(BaseModel):
    usuario: str
    senha: str
    nome: str
    id_empresas: int
    perfil: str = "barbeiro"

class ProfissionalCreate(BaseModel):
    nome: str
    cargo: str
    id_empresas: int

class ServicoCreate(BaseModel):
    nome: str
    preco: float
    duracao: int # em minutos
    id_empresas: int

class LoginRequest(BaseModel):
    usuario: str
    senha: str

# --- ROTA DE LOGIN (A que já testamos) ---

@router.post("/login")
def login(dados: LoginRequest):
    query = supabase.table("usuarios") \
        .select("id, usuario, nome, id_empresas, perfil") \
        .eq("usuario", dados.usuario) \
        .eq("senha", dados.senha) \
        .execute()

    if len(query.data) > 0:
        user = query.data[0]
        return {
            "status": "success",
            "nome": user["nome"],
            "salao_id": user["id_empresas"],
            "perfil": user["perfil"] 
        }
    raise HTTPException(status_code=401, detail="Credenciais inválidas.")

# --- CRUD: EMPRESAS ---

@router.get("/empresas")
def listar_empresas():
    res = supabase.table("empresas").select("*").order("criado_em").execute()
    return res.data

@router.post("/empresas")
def criar_empresa(dados: EmpresaCreate):
    vencimento = (datetime.now() + timedelta(days=7)).date()
    nova_empresa = {
        "nome_empresa": dados.nome,
        "whatsapp_numero": dados.whatsapp_responsavel,
        "plano": dados.plano,
        "status": "trial",
        "slug": slugify(dados.nome),
        "data_vencimento": str(vencimento)
    }
    res = supabase.table("empresas").insert(nova_empresa).execute()
    return res.data

@router.delete("/empresas/{id}")
def deletar_empresa(id: int):
    supabase.table("empresas").delete().eq("id", id).execute()
    return {"status": "removido"}

# --- CRUD: USUÁRIOS ---

@router.get("/usuarios")
def listar_usuarios():
    res = supabase.table("usuarios").select("*, empresas(nome_empresa)").execute()
    return res.data

@router.post("/usuarios")
def criar_usuario(dados: UsuarioCreate):
    res = supabase.table("usuarios").insert(dados.dict()).execute()
    return res.data

@router.delete("/usuarios/{id}")
def deletar_usuario(id: int):
    supabase.table("usuarios").delete().eq("id", id).execute()
    return {"status": "removido"}

# --- CRUD: PROFISSIONAIS ---

@router.get("/profissionais")
def listar_profissionais():
    res = supabase.table("profissionais").select("*, empresas(nome_empresa)").execute()
    return res.data

@router.post("/profissionais")
def criar_profissional(dados: ProfissionalCreate):
    res = supabase.table("profissionais").insert(dados.dict()).execute()
    return res.data

@router.delete("/profissionais/{id}")
def deletar_profissional(id: int):
    supabase.table("profissionais").delete().eq("id", id).execute()
    return {"status": "removido"}

# --- CRUD: SERVIÇOS ---

@router.get("/servicos")
def listar_servicos():
    res = supabase.table("servicos").select("*, empresas(nome_empresa)").execute()
    return res.data

@router.post("/servicos")
def criar_servico(dados: ServicoCreate):
    res = supabase.table("servicos").insert(dados.dict()).execute()
    return res.data

@router.delete("/servicos/{id}")
def deletar_servico(id: int):
    supabase.table("servicos").delete().eq("id", id).execute()
    return {"status": "removido"}

# --- CRUD: AGENDAMENTOS (Apenas Leitura e Remoção por segurança) ---

@router.get("/agendamentos")
def listar_agendamentos():
    res = supabase.table("agendamentos").select("*, empresas(nome), profissionais(nome), servicos(nome)").execute()
    return res.data

@router.delete("/agendamentos/{id}")
def deletar_agendamento(id: int):
    supabase.table("agendamentos").delete().eq("id", id).execute()
    return {"status": "removido"}