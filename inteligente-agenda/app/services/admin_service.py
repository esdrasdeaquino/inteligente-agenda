import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from app.database import supabase

# Configuração local (sem arquivo config externo)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

logger = logging.getLogger(__name__)

# --- TOOLS DE GESTÃO (EXCLUSIVAS DO DONO) ---

def relatorio_agendamentos(empresa_id: int, data_iso: str = None, status: str = None):
    """
    Lista agendamentos. Se status='cancelado', mostra quem desistiu.
    """
    data_alvo = data_iso if data_iso else datetime.now().date().isoformat()
    
    query = supabase.table("agendamentos")\
        .select("id, data_hora, nome_cliente, status, servicos(nome, preco), profissionais(nome)")\
        .eq("empresa_id", empresa_id)\
        .gte("data_hora", f"{data_alvo}T00:00:00")\
        .lte("data_hora", f"{data_alvo}T23:59:59")
    
    if status:
        query = query.eq("status", status)
        
    res = query.execute()
    return res.data if res.data else "Nenhum registro encontrado para este filtro."

def bloquear_agenda_barbearia(empresa_id: int, data_inicio: str, data_fim: str, motivo: str):
    """
    Bloqueia a barbearia inteira (ex: Feriado ou Reforma).
    """
    dados = {
        "empresa_id": empresa_id,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "motivo": motivo
    }
    res = supabase.table("disponibilidades_empresa_excecao").insert(dados).execute()
    return f"Barbearia bloqueada de {data_inicio} até {data_fim}. Motivo: {motivo}"

def folga_profissional(profissional_id: int, data_inicio: str, data_fim: str, motivo: str):
    """
    Dá folga ou bloqueia horário de um barbeiro específico.
    """
    dados = {
        "profissional_id": profissional_id,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "motivo": motivo
    }
    res = supabase.table("disponibilidades_excecao").insert(dados).execute()
    return f"Bloqueio registrado para o profissional ID {profissional_id}."

def configurar_perfil_ia(empresa_id: int, campo: str, valor: str):
    """
    Altera configurações como nome_ia, estilo ou cidade via chat.
    """
    # Lista de campos permitidos para evitar SQL Injection ou alterações indevidas
    campos_validos = ["ia_nome", "ia_estilo", "ia_genero", "cidade"]
    if campo not in campos_validos:
        return "Campo de configuração inválido."
        
    supabase.table("empresas").update({campo: valor}).eq("id", empresa_id).execute()
    return f"Configuração '{campo}' atualizada para '{valor}' com sucesso!"

# --- MOTOR DE IA DO ADMIN ---

def processar_mensagem_admin(empresa_id: int, mensagem: str, historico: list = []):
    res = supabase.table("empresas").select("*").eq("id", empresa_id).single().execute()
    emp = res.data

    # Prompt focado em GESTÃO e OPERAÇÃO
    prompt_admin = f"""
    Você é o Assistente de Gestão do salão {emp['nome_empresa']}.
    Sua função é ajudar o dono a controlar o negócio. Seja direto, eficiente e analítico.

    COMANDOS DE GESTOR:
    1. Relatórios: Se ele perguntar 'quem vem hoje' ou 'teve cancelamento', use 'relatorio_agendamentos'.
    2. Bloqueios: Se ele disser 'vou fechar amanhã' ou 'fulano vai folgar', use as ferramentas de bloqueio.
    3. Respostas: Apresente os dados em listas claras ou tabelas de texto simples.

    Data atual: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """

    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash-lite',
        tools=[relatorio_agendamentos, bloquear_agenda_barbearia, folga_profissional, configurar_perfil_ia],
        system_instruction=prompt_admin
    )

    chat = model.start_chat(history=historico, enable_automatic_function_calling=True)
    response = chat.send_message(mensagem)
    
    return {"resposta": response.text, "historico": chat.history}