import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega o arquivo .env
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")


supabase: Client = create_client(url, key)
print("✅ Conexão configurada!")


def verificar_banco():
    try:
        # Tenta ler a tabela 'empresas'
        res = supabase.table("empresas").select("*").execute()
        print("✅ SUCESSO: O Python conseguiu ler o seu banco!")
        print(f"📡 Você tem {len(res.data)} salões cadastrados.")
    except Exception as e:
        print("❌ ERRO: Ocorreu um problema na conexão.")
        print(f"Detalhe do erro: {e}")

if __name__ == "__main__":
    #verificar_banco()
    print(supabase.table("empresas").select("*").eq("nome_barbearia", "Teste").execute())
    print()


