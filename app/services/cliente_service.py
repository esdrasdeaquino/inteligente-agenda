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
    id_limpo = int(float(empresa_id))
    print(f"🔍 DEBUG: IA chamou buscar_info_gerais para empresa ID: {id_limpo}")

    # 1. Busca Profissionais
    pros = supabase.table("profissionais").select("id, nome").eq("empresa_id", id_limpo).execute()
    
    # 2. Busca Serviços
    servs = supabase.table("servicos").select("id, nome, preco, duracao_minutos").eq("empresa_id", id_limpo).execute()
    
    # 3. Busca Horários (CONFIRA SE O NOME DA TABELA ESTÁ IGUAL AO SUPABASE)
    horarios = supabase.table("horarios_funcionamento").select("*").eq("empresa_id", id_limpo).execute()

    # O PRINT QUE VOCÊ PRECISA VER:
    print(f"✅ DADOS RECUPERADOS:")
    print(f"--- Barbeiros: {len(pros.data)}")
    print(f"--- Serviços: {len(servs.data)}")
    print(f"--- Horários: {horarios.data}") # <--- Se aqui vier [], o erro é no Banco!

    qtd_barbeiros = len(pros.data)
    so_tem_um = qtd_barbeiros == 1
    
    return {
        "barbeiros": pros.data, 
        "servicos": servs.data,
        "horarios_funcionamento_semanal": horarios.data,
        "so_tem_um_barbeiro": so_tem_um,
        "nome_unico_barbeiro": pros.data[0]['nome'] if so_tem_um else None,
        "id_unico_barbeiro": pros.data[0]['id'] if so_tem_um else None
    }

def verificar_disponibilidade_total(empresa_id: int, profissional_id: int, servico_id: int, data_hora_iso: str):

    print(f"DEBUG: Verificando vaga para (horario)...")
    # 1. Pegamos a duração do serviço escolhido
    id_empresa_limpo = int(float(empresa_id))
    id_profissional_limpo = int(float(profissional_id))
    id_servico_limpo = int(float(servico_id))


    servico = supabase.table("servicos").select("duracao_minutos").eq("id", id_servico_limpo).single().execute()
    duracao = servico.data['duracao_minutos']
    
    # 2. Calculamos o intervalo que o cliente QUER ocupar
    inicio_novo = datetime.fromisoformat(data_hora_iso)
    fim_novo = inicio_novo + timedelta(minutes=duracao)

    # 3. A QUERY MÁGICA:
    # Procuramos agendamentos onde:
    # (Início do existente < Fim do novo) E (Fim do existente > Início do novo)
    conflitos = supabase.table("agendamentos")\
        .select("nome_cliente, data_hora_inicio, data_hora_fim")\
        .eq("profissional_id", id_profissional_limpo)\
        .neq("status", "cancelado")\
        .lt("data_hora_inicio", fim_novo.isoformat()) \
        .gt("data_hora_fim", inicio_novo.isoformat()) \
        .execute()

    if conflitos.data:
        # Se cair aqui, significa que o novo agendamento "atropelaria" alguém
        c = conflitos.data[0]
        return f"Indisponível. Esse serviço termina às {fim_novo.strftime('%H:%M')}, mas já existe um compromisso que começa ou termina nesse intervalo."

    # 4. Fazemos o mesmo para as folgas (Exceções)
    bloqueios = supabase.table("disponibilidades_excecao")\
        .select("motivo")\
        .eq("profissional_id", id_profissional_limpo)\
        .lt("data_inicio", fim_novo.isoformat())\
        .gt("data_fim", inicio_novo.isoformat())\
        .execute()

    if bloqueios.data:
        return f"Indisponível: O barbeiro tem um bloqueio ({bloqueios.data[0]['motivo']}) nesse período."

    return "Livre"

def verificar_expediente(empresa_id: int, data_hora_iso: str):
    """Verifica se a data/hora está dentro do horário de funcionamento da barbearia."""
    
    # 1. Limpeza de dados
    id_limpo = int(float(empresa_id))
    dt = datetime.fromisoformat(data_hora_iso)
    
    # 2. Padrão ISO: 1=Segunda, 5=Sexta (Bate com seu print do Supabase)
    dia_idx = dt.isoweekday() 
    hora_solicitada = dt.time()

    # DEBUG para você ver no terminal o que está sendo enviado ao banco
    print(f"DEBUG: Empresa {id_limpo} | Dia {dia_idx} | Hora {hora_solicitada}")

    res = supabase.table("horarios_funcionamento")\
        .select("horario_abertura, horario_fechamento")\
        .eq("empresa_id", id_limpo)\
        .eq("dia_semana", dia_idx)\
        .execute()

    # 3. Se o banco não retornou nada, é porque não abre nesse dia (ex: Domingo)
    if not res.data:
        return "A barbearia não abre neste dia da semana."

    # 4. Converte os horários do banco para comparação
    abertura = datetime.strptime(res.data[0]['horario_abertura'], "%H:%M:%S").time()
    fechamento = datetime.strptime(res.data[0]['horario_fechamento'], "%H:%M:%S").time()

    # 5. Validação de horário (Uso >= para não deixar marcar exatamente na hora de fechar)
    if hora_solicitada < abertura or hora_solicitada >= fechamento:
        return f"Fora do expediente. Abrimos às {abertura.strftime('%H:%M')} e fechamos às {fechamento.strftime('%H:%M')}."

    return "Dentro do expediente"

def recuperar_historico(empresa_id: int, whatsapp_cliente: str, limite: int = 10):
    id_limpo = int(float(empresa_id))
    try:
        res = supabase.table("historico_mensagens")\
            .select("role, content")\
            .eq("empresa_id", id_limpo)\
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
    id_limpo = int(float(empresa_id))
    try:
        data = {
            "empresa_id": id_limpo,
            "whatsapp_cliente": whatsapp_cliente,
            "role": role,
            "content": conteudo
        }
        supabase.table("historico_mensagens").insert(data).execute()
    except Exception as e:
        logger.error(f"Erro ao salvar mensagem ({role}): {e}")

def listar_horarios_livres(empresa_id: int, profissional_id: int, servico_id: int, data_iso: str):
    # 1. Casting de segurança (O terror do 1.0)
    id_empresa_limpo = int(float(empresa_id))
    id_profissional_limpo = int(float(profissional_id))
    id_servico_limpo = int(float(servico_id))
    
    dt_alvo = datetime.fromisoformat(data_iso)
    
    # 2. Sincronia com o Banco (Padrão ISO: 1=Segunda, 5=Sexta, 7=Domingo)
    # Isso resolve o erro da IA dizer que está fechado na sexta (hoje)!
    dia_semana = dt_alvo.isoweekday() 
    
    expediente = supabase.table("horarios_funcionamento")\
        .select("horario_abertura, horario_fechamento")\
        .eq("empresa_id", id_empresa_limpo)\
        .eq("dia_semana", dia_semana)\
        .execute()

    if not expediente.data:
        return "A barbearia não abre neste dia."

    # 3. Define os limites do dia
    hora_inicio = datetime.strptime(expediente.data[0]['horario_abertura'], "%H:%M:%S").time()
    hora_fim = datetime.strptime(expediente.data[0]['horario_fechamento'], "%H:%M:%S").time()
    
    horarios_disponiveis = []
    atual = datetime.combine(dt_alvo.date(), hora_inicio)
    limite = datetime.combine(dt_alvo.date(), hora_fim)

    # 4. Varredura Inteligente
    # Pegamos a hora agora para não sugerir o passado se for o mesmo dia
    agora = datetime.now()

    while atual < limite:
        # Só sugere se o horário for no futuro (comparando com o relógio agora)
        if atual > agora:
            # Reutiliza sua lógica blindada!
            status = verificar_disponibilidade_total(
                id_empresa_limpo, 
                id_profissional_limpo, 
                id_servico_limpo, 
                atual.isoformat()
            )
            
            if status == "Livre":
                horarios_disponiveis.append(atual.strftime("%H:%M"))
        
        atual += timedelta(minutes=30)

    if not horarios_disponiveis:
        return "Infelizmente não há mais horários disponíveis para hoje. Deseja verificar outro dia?"

    return f"Os horários disponíveis para {dt_alvo.strftime('%d/%m')} são: {', '.join(horarios_disponiveis)}"

def cancelar_agendamento_cliente(whatsapp_cliente: str, agendamento_id: int = None):
    """
    Cancela um agendamento do cliente. 
    Se o agendamento_id não for passado, busca os agendamentos ativos do número.
    """
    # 1. Se não tiver ID, busca o que está em aberto para esse número
    if not agendamento_id:
        res = supabase.table("agendamentos")\
            .select("id, data_hora_inicio, servicos(nome)")\
            .eq("cliente_contato", whatsapp_cliente)\
            .in_("status", ["pendente", "confirmado"])\
            .gte("data_hora_inicio", datetime.now().isoformat())\
            .execute()
        
        if not res.data:
            return "Não encontrei nenhum agendamento ativo para o seu número."
        
        if len(res.data) > 1:
            opcoes = [f"ID {a['id']}: {a['servicos']['nome']} em {a['data_hora_inicio']}" for a in res.data]
            return f"Você tem mais de um agendamento. Qual deseja cancelar? {', '.join(opcoes)}"
        
        agendamento_id = res.data[0]['id']

    # 2. Executa o cancelamento (Soft Delete - apenas muda o status)
    res_cancel = supabase.table("agendamentos")\
        .update({"status": "cancelado"})\
        .eq("id", agendamento_id)\
        .eq("cliente_contato", whatsapp_cliente)\
        .execute()

    if res_cancel.data:
        return "Pronto! Seu agendamento foi cancelado com sucesso."
    
    return "Não consegui cancelar esse agendamento. Verifique se o ID está correto."


def salvar_agendamento(empresa_id: int, profissional_id: int, servico_id: int, nome_cliente: str, whatsapp_cliente: str, data_hora_iso: str):

    # 1. Blindagem de tipagem (Casting)
    id_empresa_limpo = int(float(empresa_id))
    id_profissional_limpo = int(float(profissional_id))
    id_servico_limpo = int(float(servico_id))

    # 2. Cancela agendamentos anteriores 'pendentes' ou 'confirmados' deste cliente
    # Isso evita que o cliente fique com dois horários ao tentar "adiar" ou "mudar"
    supabase.table("agendamentos")\
        .update({"status": "cancelado"})\
        .eq("cliente_contato", whatsapp_cliente)\
        .in_("status", ["pendente", "confirmado"])\
        .execute()

    # 3. Busca duração para calcular o fim
    servico = supabase.table("servicos").select("duracao_minutos").eq("id", id_servico_limpo).single().execute()
    duracao = servico.data['duracao_minutos']
    
    inicio = datetime.fromisoformat(data_hora_iso)
    fim = inicio + timedelta(minutes=duracao)

    # 4. Prepara os dados com o status 'pendente'
    dados = {
        "empresa_id": id_empresa_limpo,
        "profissional_id": id_profissional_limpo,
        "servico_id": id_servico_limpo,
        "nome_cliente": nome_cliente,
        "cliente_contato": whatsapp_cliente,
        "data_hora_inicio": data_hora_iso,
        "data_hora_fim": fim.isoformat(),
        "status": "pendente" # <--- Agora seguindo sua regra de negócio
    }

    # 5. Insere o novo agendamento
    supabase.table("agendamentos").insert(dados).execute()

    return f"Agendamento solicitado para as {inicio.strftime('%H:%M')}! Ficou como pendente e enviaremos uma mensagem para confirmação 1 hora antes do corte."

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
    # PERSONA E CONTEXTO
    Você é {nome_ia}, o braço direito do(a) {segmento} {emp['nome_empresa']} em {cidade}. 
    Seu objetivo é agendar serviços de forma rápida, sem burocracia e com foco total nos dados reais.
    Cliente: {whatsapp_cliente} | Data/Hora Atual: {datetime.now().strftime('%d/%m/%Y %H:%M')} (Sexta-feira).

    # DIRETRIZ SUPREMA (NÃO IGNORE)
    1. PROIBIDO INVENTAR: Nunca invente nomes de profissionais, preços, serviços ou horários. 
    2. CONSULTA OBRIGATÓRIA: Antes de dar qualquer informação sobre a empresa (mesmo um 'Oi'), você DEVE chamar a função 'buscar_info_gerais'. 
    3. EXPEDIENTE: Para saber se abrimos hoje ou em qualquer dia, use os dados retornados por 'buscar_info_gerais' (campo horarios_funcionamento_semanal). 

    # TOM DE VOZ: {estilo}
    - Se 'Engraçado': Seja resenheiro, use o sotaque de {cidade} (ex: "massa", "visse", "oxe", "tabacudo", "relaxe"). Trate o cliente como um 'parça' da barbearia.
    - Se 'Sério': Seja direto, formal e use termos como "Prezado" e "Cordialmente".
    - Se 'Profissional': Seja cordial, eficiente e use emojis de forma moderada ✂️.

    # LÓGICA DE EXECUÇÃO (FLOW)
    - IDENTIFICAÇÃO: Se o histórico estiver vazio, apresente-se e já chame 'buscar_info_gerais'. 
    - PROFISSIONAIS: Se a função retornar que 'so_tem_um_barbeiro' é True, não pergunte a preferência. Use o nome que vier em 'nome_unico_barbeiro' e confirme o atendimento direto.
    - DISPONIBILIDADE: Ao receber uma data/hora, use 'verificar_disponibilidade_total'. Se der 'Indisponível', chame IMEDIATAMENTE 'listar_horarios_livres' e ofereça as opções.
    - REAGENDAMENTO: Adiar = 'cancelar_agendamento' (do antigo) + 'salvar_agendamento' (do novo). Informe ao cliente que o antigo foi liberado.

    # REGRAS DE NEGÓCIO E UX
    - STATUS: Todos os novos agendamentos são salvos como 'pendente'. Explique que ele receberá uma confirmação 1h antes.
    - CANCELAMENTO: Se o cliente quiser cancelar, use 'cancelar_agendamento_cliente' usando o WhatsApp {whatsapp_cliente}. Nunca peça IDs complicados.
    - PROATIVIDADE: Preço e duração andam juntos. Se falar o preço, diga quanto tempo leva.
    - MEMÓRIA: Consulte o histórico para não perguntar o nome do cliente mais de uma vez.
    - Você é proibido de dizer 'não sei' ou 'não encontrei' sem antes chamar a função buscar_info_gerais. Se o cliente perguntar qualquer coisa sobre a empresa, chame a função primeiro, leia o campo horarios_funcionamento_semanal e responda baseado nisso.
    """

    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        tools=[
            buscar_info_gerais, 
            verificar_disponibilidade_total, 
            salvar_agendamento, 
            listar_horarios_livres, 
            cancelar_agendamento_cliente,
            verificar_expediente
        ],
        system_instruction=prompt_final
    )

    # Inicia o chat com o histórico vindo do banco/webhook
    chat = model.start_chat(history=historico_formatado, enable_automatic_function_calling=True)
    response = chat.send_message(mensagem)

    usage = response.usage_metadata
    print(f"""
    📊 CONSUMO DE TOKENS:
    - Prompt (Entrada + Histórico): {usage.prompt_token_count}
    - Resposta (Saída da IA): {usage.candidates_token_count}
    - Total: {usage.total_token_count}
    """)

    try:
        resposta_texto = response.text
    except Exception as e:
        # Caso a IA ainda queira chamar algo ou dê erro, pegamos a última parte disponível
        print(f"Erro ao captar texto: {e}")
        resposta_texto = response.candidates[0].content.parts[0].text if response.candidates[0].content.parts else "Desculpe, tive um problema ao processar sua solicitação."
   


    #resposta_texto = response.text
    
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