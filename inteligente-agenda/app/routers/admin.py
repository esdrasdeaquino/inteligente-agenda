from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase, verificar_admin
from pydantic import BaseModel
from typing import List, Optional
from slugify import slugify
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])

# ==========================================
# SCHEMAS (VALIDAÇÃO DE DADOS)
# ==========================================

class LoginRequest(BaseModel):
    usuario: str
    senha: str

class EmpresaCreate(BaseModel):
    nome_empresa: str
    whatsapp_numero: str
    plano: Optional[str] = "essencial"
    status: Optional[str] = "ativo"
    whatsapp_dono: Optional[str] = None
    cidade: Optional[str] = None
    instancia: Optional[str] = None
    segmento: Optional[str] = "Salão"
    ia_nome: Optional[str] = None
    ia_estilo: Optional[str] = None
    verificar_cliente: Optional[bool] = False

class EmpresaUpdate(EmpresaCreate):
    nome_empresa: Optional[str] = None
    whatsapp_numero: Optional[str] = None

class UsuarioCreate(BaseModel):
    usuario: str
    senha: str
    nome: str
    id_empresas: int
    perfil: Optional[str] = "user"

class UsuarioUpdate(BaseModel):
    usuario: Optional[str] = None
    senha: Optional[str] = None
    nome: Optional[str] = None
    id_empresas: Optional[int] = None
    perfil: Optional[str] = None

class ProfissionalCreate(BaseModel):
    empresa_id: int
    nome: str
    ativo: Optional[bool] = True

class ProfissionalUpdate(BaseModel):
    empresa_id: Optional[int] = None
    nome: Optional[str] = None
    ativo: Optional[bool] = None

class ServicoCreate(BaseModel):
    empresa_id: int
    nome: str
    preco: str # No seu BD preco é TEXT
    duracao_minutos: Optional[int] = 30

class ServicoUpdate(BaseModel):
    empresa_id: Optional[int] = None
    nome: Optional[str] = None
    preco: Optional[str] = None
    duracao_minutos: Optional[int] = None

class AgendamentoCreate(BaseModel):
    empresa_id: int
    profissional_id: int
    servico_id: int
    nome_cliente: str
    cliente_contato: str
    data_hora_inicio: str
    data_hora_fim: str
    status: Optional[str] = "pendente"

class AgendamentoUpdate(BaseModel):
    empresa_id: Optional[int] = None
    profissional_id: Optional[int] = None
    servico_id: Optional[int] = None
    nome_cliente: Optional[str] = None
    cliente_contato: Optional[str] = None
    data_hora_inicio: Optional[str] = None
    data_hora_fim: Optional[str] = None
    status: Optional[str] = None

class HorarioCreate(BaseModel):
    empresa_id: int
    dia_semana: int
    horario_abertura: str
    horario_fechamento: str

class HorarioUpdate(BaseModel):
    empresa_id: Optional[int] = None
    dia_semana: Optional[int] = None
    horario_abertura: Optional[str] = None
    horario_fechamento: Optional[str] = None

class ExcecaoEmpresaCreate(BaseModel):
    empresa_id: int
    data_inicio: str
    data_fim: str
    motivo: Optional[str] = None

class ExcecaoEmpresaUpdate(BaseModel):
    empresa_id: Optional[int] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    motivo: Optional[str] = None

class ExcecaoProfissionalCreate(BaseModel):
    profissional_id: int
    data_inicio: str
    data_fim: str
    motivo: Optional[str] = None

class ExcecaoProfissionalUpdate(BaseModel):
    profissional_id: Optional[int] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    motivo: Optional[str] = None

class ServicoProfissionalCreate(BaseModel):
    profissional_id: int
    servico_id: int
    empresa_id: int

class ServicoProfissionalUpdate(BaseModel):
    profissional_id: Optional[int] = None
    servico_id: Optional[int] = None
    empresa_id: Optional[int] = None

class HistoricoCreate(BaseModel):
    empresa_id: int
    whatsapp_cliente: str
    role: str
    content: str

class HistoricoUpdate(BaseModel):
    empresa_id: Optional[int] = None
    whatsapp_cliente: Optional[str] = None
    role: Optional[str] = None
    content: Optional[str] = None

# ==========================================
# ROTA DE LOGIN
# ==========================================

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

# ==========================================
# FUNÇÕES AUXILIARES DE CRUD
# ==========================================

def criar_registro(tabela: str, dados: dict):
    res = supabase.table(tabela).insert(dados).execute()
    return res.data

def atualizar_registro(tabela: str, id_valor: any, dados: dict):
    update_data = {k: v for k, v in dados.items() if v is not None}
    res = supabase.table(tabela).update(update_data).eq("id", id_valor).execute()
    return res.data

def deletar_registro(tabela: str, id_valor: any):
    supabase.table(tabela).delete().eq("id", id_valor).execute()
    return {"status": "removido"}

# ==========================================
# ROTAS EMPRESAS
# ==========================================
@router.get("/empresas")
def listar_empresas():
    return supabase.table("empresas").select("*").order("criado_em").execute().data

@router.post("/empresas")
def criar_empresa(dados: EmpresaCreate):
    vencimento = (datetime.now() + timedelta(days=30)).date() # Default 30 dias do seu BD
    nova_empresa = dados.dict()
    nova_empresa["slug"] = slugify(dados.nome_empresa)
    nova_empresa["data_expiracao"] = str(vencimento)
    return criar_registro("empresas", nova_empresa)

@router.put("/empresas/{id}")
def editar_empresa(id: int, dados: EmpresaUpdate):
    update_data = dados.dict(exclude_unset=True)
    if "nome_empresa" in update_data and update_data["nome_empresa"]:
        update_data["slug"] = slugify(update_data["nome_empresa"])
    return atualizar_registro("empresas", id, update_data)

@router.delete("/empresas/{id}")
def remover_empresa(id: int):
    return deletar_registro("empresas", id)

# ==========================================
# ROTAS USUÁRIOS
# ==========================================
@router.get("/usuarios")
def listar_usuarios():
    return supabase.table("usuarios").select("*, empresas(nome_empresa)").execute().data

@router.post("/usuarios")
def criar_usuario(dados: UsuarioCreate):
    return criar_registro("usuarios", dados.dict())

@router.put("/usuarios/{id}")
def editar_usuario(id: str, dados: UsuarioUpdate):
    return atualizar_registro("usuarios", id, dados.dict(exclude_unset=True))

@router.delete("/usuarios/{id}")
def remover_usuario(id: str):
    return deletar_registro("usuarios", id)

# ==========================================
# ROTAS PROFISSIONAIS
# ==========================================
@router.get("/profissionais")
def listar_profissionais():
    return supabase.table("profissionais").select("*, empresas(nome_empresa)").execute().data

@router.post("/profissionais")
def criar_profissional(dados: ProfissionalCreate):
    return criar_registro("profissionais", dados.dict())

@router.put("/profissionais/{id}")
def editar_profissional(id: int, dados: ProfissionalUpdate):
    return atualizar_registro("profissionais", id, dados.dict(exclude_unset=True))

@router.delete("/profissionais/{id}")
def remover_profissional(id: int):
    return deletar_registro("profissionais", id)

# ==========================================
# ROTAS SERVIÇOS
# ==========================================
@router.get("/servicos")
def listar_servicos():
    return supabase.table("servicos").select("*, empresas(nome_empresa)").execute().data

@router.post("/servicos")
def criar_servico(dados: ServicoCreate):
    return criar_registro("servicos", dados.dict())

@router.put("/servicos/{id}")
def editar_servico(id: int, dados: ServicoUpdate):
    return atualizar_registro("servicos", id, dados.dict(exclude_unset=True))

@router.delete("/servicos/{id}")
def remover_servico(id: int):
    return deletar_registro("servicos", id)

# ==========================================
# ROTAS AGENDAMENTOS (ATUALIZADA)
# ==========================================
@router.get("/agendamentos")
def listar_agendamentos():
    # Adicionado preco e duracao_minutos na seleção da tabela de serviços
    return supabase.table("agendamentos").select("*, empresas(nome_empresa), profissionais(nome), servicos(nome, preco, duracao_minutos)").execute().data

@router.post("/agendamentos")
def criar_agendamento(dados: AgendamentoCreate):
    return criar_registro("agendamentos", dados.dict())

@router.put("/agendamentos/{id}")
def editar_agendamento(id: int, dados: AgendamentoUpdate):
    return atualizar_registro("agendamentos", id, dados.dict(exclude_unset=True))

@router.delete("/agendamentos/{id}")
def remover_agendamento(id: int):
    return deletar_registro("agendamentos", id)

# ==========================================
# ROTAS HORARIOS_FUNCIONAMENTO
# ==========================================
@router.get("/horarios_funcionamento")
def listar_horarios():
    return supabase.table("horarios_funcionamento").select("*, empresas(nome_empresa)").execute().data

@router.post("/horarios_funcionamento")
def criar_horario(dados: HorarioCreate):
    return criar_registro("horarios_funcionamento", dados.dict())

@router.put("/horarios_funcionamento/{id}")
def editar_horario(id: int, dados: HorarioUpdate):
    return atualizar_registro("horarios_funcionamento", id, dados.dict(exclude_unset=True))

@router.delete("/horarios_funcionamento/{id}")
def remover_horario(id: int):
    return deletar_registro("horarios_funcionamento", id)

# ==========================================
# ROTAS DISPONIBILIDADES_EMPRESA_EXCECAO
# ==========================================
@router.get("/disponibilidades_empresa_excecao")
def listar_excecoes_empresa():
    return supabase.table("disponibilidades_empresa_excecao").select("*, empresas(nome_empresa)").execute().data

@router.post("/disponibilidades_empresa_excecao")
def criar_excecao_empresa(dados: ExcecaoEmpresaCreate):
    return criar_registro("disponibilidades_empresa_excecao", dados.dict())

@router.put("/disponibilidades_empresa_excecao/{id}")
def editar_excecao_empresa(id: int, dados: ExcecaoEmpresaUpdate):
    return atualizar_registro("disponibilidades_empresa_excecao", id, dados.dict(exclude_unset=True))

@router.delete("/disponibilidades_empresa_excecao/{id}")
def remover_excecao_empresa(id: int):
    return deletar_registro("disponibilidades_empresa_excecao", id)

# ==========================================
# ROTAS DISPONIBILIDADES_EXCECAO (PROFISSIONAL)
# ==========================================
@router.get("/disponibilidades_excecao")
def listar_excecoes_profissional():
    return supabase.table("disponibilidades_excecao").select("*, profissionais(nome)").execute().data

@router.post("/disponibilidades_excecao")
def criar_excecao_profissional(dados: ExcecaoProfissionalCreate):
    return criar_registro("disponibilidades_excecao", dados.dict())

@router.put("/disponibilidades_excecao/{id}")
def editar_excecao_profissional(id: int, dados: ExcecaoProfissionalUpdate):
    return atualizar_registro("disponibilidades_excecao", id, dados.dict(exclude_unset=True))

@router.delete("/disponibilidades_excecao/{id}")
def remover_excecao_profissional(id: int):
    return deletar_registro("disponibilidades_excecao", id)

# ==========================================
# ROTAS SERVICOS_PROFISSIONAIS
# ==========================================
@router.get("/servicos_profissionais")
def listar_servicos_profissionais():
    return supabase.table("servicos_profissionais").select("*, profissionais(nome), servicos(nome), empresas(nome_empresa)").execute().data

@router.post("/servicos_profissionais")
def criar_servicos_profissionais(dados: ServicoProfissionalCreate):
    return criar_registro("servicos_profissionais", dados.dict())

@router.put("/servicos_profissionais/{id}")
def editar_servicos_profissionais(id: int, dados: ServicoProfissionalUpdate):
    return atualizar_registro("servicos_profissionais", id, dados.dict(exclude_unset=True))

@router.delete("/servicos_profissionais/{id}")
def remover_servicos_profissionais(id: int):
    return deletar_registro("servicos_profissionais", id)

# ==========================================
# ROTAS HISTORICO_MENSAGENS
# ==========================================
@router.get("/historico_mensagens")
def listar_historico():
    return supabase.table("historico_mensagens").select("*, empresas(nome_empresa)").execute().data

@router.post("/historico_mensagens")
def criar_historico(dados: HistoricoCreate):
    return criar_registro("historico_mensagens", dados.dict())

@router.put("/historico_mensagens/{id}")
def editar_historico(id: str, dados: HistoricoUpdate):
    return atualizar_registro("historico_mensagens", id, dados.dict(exclude_unset=True))

@router.delete("/historico_mensagens/{id}")
def remover_historico(id: str):
    return deletar_registro("historico_mensagens", id)