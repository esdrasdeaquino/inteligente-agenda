import google.generativeai as genai
import os
import logging # <--- NOVO
from dotenv import load_dotenv
from app.database import supabase

# Configura o log para aparecer no terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)



# 1. Definimos a "Ferramenta" que a IA pode usar
def contar_barbearias_no_banco():
    """Retorna o número total de barbearias cadastradas no sistema."""
    res = supabase.table("empresas").select("*", count="exact").execute()
    return f"Existem {res.count} barbearias cadastradas."

def cadastrar_nova_barbearia(nome: str, whatsapp: str, plano: str):
    """Cadastra uma nova barbearia no sistema. Retorna o ID gerado."""
    novo = {
        "nome_empresa": nome,
        "whatsapp_numero": whatsapp,
        "plano": plano, # Valor padrão
    }
    res = supabase.table("empresas").insert(novo).execute()
    
    if res.data:
        id_gerado = res.data[0]['id']
        return f"Barbearia '{nome}' cadastrada com sucesso! O ID dela é {id_gerado}."
    return "Erro ao cadastrar barbearia."

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite',
    tools=[
        cadastrar_nova_barbearia # <--- ADICIONE AQUI
    ]
)

# 3. Função para processar a pergunta do usuário
def processar_pergunta_admin(pergunta: str):
    # EM VEZ DE PRINT, VAMOS USAR O LOGGER
    logger.info(f"--- INICIANDO CONSULTA IA: {pergunta} ---")
    
    try:
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(pergunta)
        
        if response.usage_metadata:
            # ISSO VAI APARECER COM UM PREFIXO "INFO" NO TERMINAL
            logger.info(f"CONSUMO TOTAL: {response.usage_metadata.total_token_count} TOKENS")
            
        return response.text
    except Exception as e:
        logger.error(f"ERRO CRÍTICO NA IA: {str(e)}")
        return f"Erro: {str(e)}"
    


