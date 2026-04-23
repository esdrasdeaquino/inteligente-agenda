import google.generativeai as genai
import os
import logging
from datetime import datetime
from app.database import supabase
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# --- FERRAMENTAS (TOOLS) QUE A IA VAI OPERAR ---

def buscar_info_gerais(empresa_id: int):
    """
    OBRIGATÓRIO: Use isso no início para conhecer barbeiros, serviços e preços.
    """
    pros = supabase.table("profissionais").select("id, nome").eq("empresa_id", empresa_id).execute()
    servs = supabase.table("servicos").select("id, nome, preco").eq("empresa_id", empresa_id).execute()
    return {"barbeiros": pros.data, "servicos": servs.data}

def verificar_disponibilidade_total(empresa_id: int, profissional_id: int, servico_id: int, data_hora_iso: str):
    # 1. Pegamos a duração do serviço escolhido
    servico = supabase.table("servicos").select("duracao_minutos").eq("id", servico_id).single().execute()
    duracao = servico.data['duracao_minutos']
    
    # 2. Calculamos o intervalo que o cliente QUER ocupar
    inicio_novo = datetime.fromisoformat(data_hora_iso)
    fim_novo = inicio_novo + timedelta(minutes=duracao)

    # 3. A QUERY MÁGICA:
    # Procuramos agendamentos onde:
    # (Início do existente < Fim do novo) E (Fim do existente > Início do novo)
    conflitos = supabase.table("agendamentos")\
        .select("nome_cliente, data_hora, horario_fim")\
        .eq("profissional_id", profissional_id)\
        .neq("status", "cancelado")\
        .lt("data_hora", fim_novo.isoformat()) \
        .gt("horario_fim", inicio_novo.isoformat()) \
        .execute()

    if conflitos.data:
        # Se cair aqui, significa que o novo agendamento "atropelaria" alguém
        c = conflitos.data[0]
        return f"Indisponível. Esse serviço termina às {fim_novo.strftime('%H:%M')}, mas já existe um compromisso que começa ou termina nesse intervalo."

    # 4. Fazemos o mesmo para as folgas (Exceções)
    bloqueios = supabase.table("disponibilidades_excecao")\
        .select("motivo")\
        .eq("profissional_id", profissional_id)\
        .lt("data_inicio", fim_novo.isoformat())\
        .gt("data_fim", inicio_novo.isoformat())\
        .execute()

    if bloqueios.data:
        return f"Indisponível: O barbeiro tem um bloqueio ({bloqueios.data[0]['motivo']}) nesse período."

    return "Livre"

def verificar_expediente(empresa_id: int, data_hora_iso: str):
    """Verifica se a data/hora está dentro do horário de funcionamento da barbearia."""
    dt = datetime.fromisoformat(data_hora_iso)
    dia_semana = dt.weekday() + 1 # Ajuste para bater com o padrão (0-6 ou 1-7)
    # No Python, Monday é 0. No Postgres, depende, então vamos padronizar.
    # Vamos usar dt.strftime('%w') para pegar 0 (Domingo) a 6 (Sábado).
    dia_idx = int(dt.strftime('%w'))
    hora_solicitada = dt.time()

    res = supabase.table("horarios_funcionamento")\
        .select("horario_abertura, horario_fechamento")\
        .eq("empresa_id", empresa_id)\
        .eq("dia_semana", dia_idx)\
        .execute()

    if not res.data:
        return "A barbearia não abre neste dia da semana."

    abertura = datetime.strptime(res.data[0]['horario_abertura'], "%H:%M:%S").time()
    fechamento = datetime.strptime(res.data[0]['horario_fechamento'], "%H:%M:%S").time()

    if hora_solicitada < abertura or hora_solicitada > fechamento:
        return f"Fora do expediente. Abrimos às {abertura.strftime('%H:%M')} e fechamos às {fechamento.strftime('%H:%M')}."

    return "Dentro do expediente"

def listar_horarios_livres(empresa_id: int, profissional_id: int, servico_id: int, data_iso: str):
    """
    Varre o dia buscando espaços vagos que caibam o serviço escolhido.
    """
    # 1. Busca o expediente da barbearia para aquele dia
    dt_alvo = datetime.fromisoformat(data_iso)
    dia_semana = int(dt_alvo.strftime('%w'))
    
    expediente = supabase.table("horarios_funcionamento")\
        .select("horario_abertura, horario_fechamento")\
        .eq("empresa_id", empresa_id).eq("dia_semana", dia_semana).execute()

    if not expediente.data:
        return "A barbearia não abre neste dia."

    # 2. Define o início e o fim da varredura
    hora_inicio = datetime.strptime(expediente.data[0]['horario_abertura'], "%H:%M:%S").time()
    hora_fim = datetime.strptime(expediente.data[0]['horario_fechamento'], "%H:%M:%S").time()
    
    # 3. Varre o dia em intervalos (ex: a cada 30 min)
    horarios_disponiveis = []
    atual = datetime.combine(dt_alvo.date(), hora_inicio)
    limite = datetime.combine(dt_alvo.date(), hora_fim)

    while atual < limite:
        # Se for para o dia de HOJE, não sugere horários que já passaram
        if atual > datetime.now():
            # REUTILIZA a função de checagem que já temos!
            status = verificar_disponibilidade_total(empresa_id, profissional_id, servico_id, atual.isoformat())
            
            if status == "Livre":
                horarios_disponiveis.append(atual.strftime("%H:%M"))
        
        atual += timedelta(minutes=30) # Pula de 30 em 30 min

    if not horarios_disponiveis:
        return "Infelizmente não há mais horários disponíveis para este profissional nesta data."

    return f"Os horários disponíveis são: {', '.join(horarios_disponiveis)}"

def cancelar_agendamento_cliente(whatsapp_cliente: str, agendamento_id: int = None):
    """
    Cancela um agendamento do cliente. 
    Se o agendamento_id não for passado, busca os agendamentos ativos do número.
    """
    # 1. Se não tiver ID, busca o que está em aberto para esse número
    if not agendamento_id:
        res = supabase.table("agendamentos")\
            .select("id, data_hora, servicos(nome)")\
            .eq("whatsapp_cliente", whatsapp_cliente)\
            .in_("status", ["pendente", "confirmado"])\
            .gte("data_hora", datetime.now().isoformat())\
            .execute()
        
        if not res.data:
            return "Não encontrei nenhum agendamento ativo para o seu número."
        
        if len(res.data) > 1:
            opcoes = [f"ID {a['id']}: {a['servicos']['nome']} em {a['data_hora']}" for a in res.data]
            return f"Você tem mais de um agendamento. Qual deseja cancelar? {', '.join(opcoes)}"
        
        agendamento_id = res.data[0]['id']

    # 2. Executa o cancelamento (Soft Delete - apenas muda o status)
    res_cancel = supabase.table("agendamentos")\
        .update({"status": "cancelado"})\
        .eq("id", agendamento_id)\
        .eq("whatsapp_cliente", whatsapp_cliente)\
        .execute()

    if res_cancel.data:
        return "Pronto! Seu agendamento foi cancelado com sucesso."
    
    return "Não consegui cancelar esse agendamento. Verifique se o ID está correto."


def salvar_agendamento(empresa_id: int, profissional_id: int, servico_id: int, nome_cliente: str, whatsapp_cliente: str, data_hora_iso: str):
    # Busca duração para gravar o fim
    servico = supabase.table("servicos").select("duracao_minutos").eq("id", servico_id).single().execute()
    duracao = servico.data['duracao_minutos']
    
    inicio = datetime.fromisoformat(data_hora_iso)
    fim = inicio + timedelta(minutes=duracao)

    dados = {
        "empresa_id": empresa_id,
        "profissional_id": profissional_id,
        "servico_id": servico_id,
        "nome_cliente": nome_cliente,
        "whatsapp_cliente": whatsapp_cliente,
        "data_hora": data_hora_iso,
        "horario_fim": fim.isoformat() # <--- Gravando o fim corretamente
    }
    supabase.table("agendamentos").insert(dados).execute()
    return f"Agendamento confirmado! O atendimento será das {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}."

# --- MOTOR DE IA ---

def processar_mensagem_cliente(empresa_id: int, whatsapp_cliente: str, mensagem: str, historico: list = []):
    # Busca os dados da empresa para personalizar o atendimento
    res = supabase.table("empresas").select("*").eq("id", empresa_id).single().execute()
    emp = res.data
    
    # Extração de variáveis do banco para o prompt
    cidade = emp.get('cidade', 'Brasil')
    estilo = emp.get('ia_estilo', 'Profissional')
    nome_ia = emp.get('ia_nome', 'Assistente')

    prompt_final = f"""
    Você é {nome_ia}, assistente do salão {emp['nome']} em {cidade}.
    O cliente com quem você fala tem o WhatsApp: {whatsapp_cliente}.

    INSTRUÇÃO DE LINGUAGEM:
    - Se {estilo} for 'Engraçado', use um tom bem-humorado e brincalhão.
    - Se {estilo} for 'Sério', seja direto, formal e evite gracinhas.
    - Se {estilo} for 'Profissional', seja cordial, educado e eficiente.

    AÇÕES POSSÍVEIS:
    1. AGENDAR: Use 'buscar_info_gerais' -> 'verificar_disponibilidade_total' -> 'salvar_agendamento'.
    2. CANCELAR: Use 'cancelar_agendamento_cliente' passando o whatsapp: {whatsapp_cliente}.
    3. SUGERIR: Se o horário estiver ocupado, use 'listar_horarios_livres'.

    REGRAS DE MEMÓRIA:
    - Verifique o histórico de mensagens para saber se o cliente já mencionou um serviço ou barbeiro antes de perguntar novamente.
    - Se o cliente disser 'quero cancelar o meu', chame a função de cancelamento sem pedir o ID primeiro.
    """

    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash-lite',
        tools=[
            buscar_info_gerais, 
            verificar_disponibilidade_total, 
            salvar_agendamento, 
            listar_horarios_livres, 
            cancelar_agendamento_cliente 
        ],
        system_instruction=prompt_final
    )

    # Inicia o chat com o histórico vindo do banco/webhook
    chat = model.start_chat(history=historico, enable_automatic_function_calling=True)
    response = chat.send_message(mensagem)
    
    return {
        "resposta": response.text, 
        "historico": chat.history # Salve isso no seu banco de conversas!
    }