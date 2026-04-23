from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import admin, barbearia, agendamentos, ia
from app.database import supabase

app = FastAPI(title="Inteligente Agenda API")

# Liberação para o seu primo conseguir acessar o Front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluindo as rotas modulares
app.include_router(admin.router)
app.include_router(barbearia.router)
app.include_router(agendamentos.router)
app.include_router(ia.router)

@app.get("/")
def home():
    return {"status": "API Online", "versao": "1.0.0"}

@app.get("/configuracao/{slug}", tags=["Cliente"])
def buscar_configuracao(slug: str):
    res = supabase.table("empresas").select("id, nome, plano, status").eq("slug", slug).execute()
    if not res.data:
        return {"erro": "Não encontrado"}
    return res.data[0]