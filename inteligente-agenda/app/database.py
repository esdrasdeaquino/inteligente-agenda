import os
from supabase import create_client
from fastapi import Header, HTTPException, Depends
from dotenv import load_dotenv

load_dotenv()

# Conexão com o Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(url)


supabase = create_client(url, key)

# Token de Segurança
ADMIN_SECRET_TOKEN = "galego84454299"

def verificar_admin(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Acesso negado: Token inválido")