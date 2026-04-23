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
    pros = supabase.table("profissionais").select("id, nome").eq("empresa_id", empresa_id).execute()
    servs = supabase.table("servicos").select("id, nome, preco, duracao_minutos").eq("empresa_id", empresa_id).execute()
    
    # Lógica para facilitar a vida da IA
    qtd_barbeiros = len(pros.data)
    so_tem_um = qtd_barbeiros == 1
    
    return {
        "barbeiros": pros.data, 
        "servicos": servs.data,
        "so_tem_um_barbeiro": so_tem_um,
        "nome_unico_barbeiro": pros.data[0]['nome'] if so_tem_um else None,
        "id_unico_barbeiro": pros.data[0]['id'] if so_tem_um else None
    }
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
def recuperar_historico(empresa_id: int, whatsapp_cliente: str, limite: int = 10):
    try:
        res = supabase.table("historico_mensagens")\
            .select("role, content")\
            .eq("empresa_id", empresa_id)\
            .eq("whatsapp_cliente", whatsapp_cliente)\
            .order("created_at", desc=True)\
            .limit(limite)\
            .execute()
        
        # Invertemos para enviar ao Gemini na ordem cronológica correta (antiga -> nova)
        return [{"role": m['role'], "parts": [m['content']]} for m in reversed(res.data)]
    except Exception as e:
        logger.error(f"Erro ao recuperar histórico: {e}")
        return [] # Se falhar, a IA começa sem contexto, mas não trava o chat

def salvar_no_historico(empresa_id: int, whatsapp_cliente: str, role: str, conteudo: str):
    try:
        data = {
            "empresa_id": empresa_id,
            "whatsapp_cliente": whatsapp_cliente,
            "role": role,
            "content": conteudo
        }
        supabase.table("historico_mensagens").insert(data).execute()
    except Exception as e:
        logger.error(f"Erro ao salvar mensagem ({role}): {e}")

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

    res_hist = supabase.table("historico_mensagens")\
        .select("role, content")\
        .eq("whatsapp_cliente", whatsapp_cliente)\
        .eq("empresa_id", empresa_id)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    # O Gemini espera o histórico do mais antigo para o mais novo, então invertemos
    historico_formatado = []
    for msg in reversed(res_hist.data):
        historico_formatado.append({"role": msg['role'], "parts": [msg['content']]})
    
    # Extração de variáveis do banco para o prompt
    cidade = emp.get('cidade', 'Brasil')
    estilo = emp.get('ia_estilo', 'Profissional')
    nome_ia = emp.get('ia_nome', 'Assistente')
    segmento = emp.get('segmento', 'Salão')

    prompt_final = f"""
    Você é {nome_ia}, assistente inteligente de um(a) {segmento} chamado {emp['nome']} em {cidade}.
    O cliente com quem você fala tem o WhatsApp: {whatsapp_cliente}.
    Data e hora atual: {datetime.now().strftime('%d/%m/%Y %H:%M')}

    INSTRUÇÃO DE LINGUAGEM:
    - Seu tom é {estilo}. 
    - Se 'Engraçado', seja resenheiro e brincalhão, Use gírias e o sotaque de {cidade} de forma natural.
    - Se 'Sério', seja direto e formal.
    - Se 'Profissional', seja cordial e eficiente.

    LÓGICA DE ATENDIMENTO (Fluxo de Agendamento):
    1. Sempre comece usando 'buscar_info_gerais' para conhecer os serviços e barbeiros disponíveis.
    2. SE HOUVER APENAS 1 PROFISSIONAL: Não pergunte com quem o cliente quer cortar. Confirme o atendimento com ele de forma direta (Ex: "O serviço vai ser com {{nome}}, beleza?").
    3. SE HOUVER MAIS DE 1 PROFISSIONAL: Apresente as opções e pergunte a preferência do cliente.
    4. Antes de agendar, você PRECISA de: Nome do Cliente, Serviço, Barbeiro e Data/Hora.

    AÇÕES E TOOLS:
    - AGENDAR: 'buscar_info_gerais' -> 'verificar_disponibilidade_total' -> 'salvar_agendamento'.
    - CANCELAR: Use 'cancelar_agendamento_cliente' sempre usando o whatsapp: {whatsapp_cliente}.
    - INDISPONIBILIDADE: Se o horário escolhido estiver ocupado, use 'listar_horarios_livres' para sugerir alternativas próximas.

    REGRAS DE MEMÓRIA E UX:
    - SEMPRE consulte o histórico. Se o cliente já disse o nome ou o serviço em mensagens anteriores, não pergunte de novo.
    - Se o cliente quiser cancelar, não peça o ID do agendamento. Tente cancelar direto pelo WhatsApp dele.
    - Seja proativo: se ele perguntar o preço, já mencione a duração do serviço.
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
    chat = model.start_chat(history=historico_formatado, enable_automatic_function_calling=True)
    response = chat.send_message(mensagem)
    resposta_texto = response.text
    
    supabase.table("historico_mensagens").insert({
        "empresa_id": empresa_id,
        "whatsapp_cliente": whatsapp_cliente,
        "role": "user",
        "content": mensagem
    }).execute()

    # Salva o que a IA respondeu
    
    supabase.table("historico_mensagens").insert({
        "empresa_id": empresa_id,
        "whatsapp_cliente": whatsapp_cliente,
        "role": "model",
        "content": resposta_texto
    }).execute()

    return {"resposta": resposta_texto}