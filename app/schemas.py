from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BarbeariaCreate(BaseModel):
    nome: str
    whatsapp_responsavel: str
    plano: str = "essencial"

class ServicoCreate(BaseModel):
    empresa_id: int
    nome: str
    preco: float
    duracao: int = 30

class ProfissionalCreate(BaseModel):
    empresa_id: int
    nome: str
    especialidade: Optional[str] = None

# O "Pulo do Gato": Para vincular vários serviços de uma vez
class VincularServicosEmMassa(BaseModel):
    profissional_id: int
    servicos_ids: List[int]

class AgendamentoCreate(BaseModel):
    empresa_id: int
    profissional_id: int
    servico_id: int
    nome_cliente: str
    whatsapp_cliente: str
    data_hora: datetime # O FastAPI converte o texto do front para data real