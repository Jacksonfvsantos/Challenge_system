import datetime
from database.conexao import supabase

# --- FUNÇÕES DE VALIDAÇÃO (Proteção contra o erro 22P02) ---
def eh_uuid_valido(valor):
    """Verifica se o ID não é vazio ou a string literal 'None'"""
    if not valor or str(valor).strip().lower() == "none" or str(valor).strip() == "":
        return False
    return True

# --- GERENCIAMENTO DE TIMES ---
def listar_times():
    try:
        resposta = supabase.table("times").select("*").order("nome").execute()
        return resposta.data or []
    except Exception as erro:
        print(f"Erro [listar_times]: {erro}")
        return []

def obter_time_do_usuario(usuario_id):
    if not eh_uuid_valido(usuario_id): return [None]
    try:
        res = supabase.table("time_membros").select("time_id").eq("usuario_id", str(usuario_id)).execute()
        return [item["time_id"] for item in res.data] if res.data else [None]
    except: return [None]

def obter_nomes_dos_times(t_a, t_b):
    nome_a, nome_b = "Time A", "Time B"
    try:
        if eh_uuid_valido(t_a):
            res_a = supabase.table("times").select("nome").eq("id", str(t_a)).execute()
            if res_a.data: nome_a = res_a.data[0]["nome"]
            
        if eh_uuid_valido(t_b):
            res_b = supabase.table("times").select("nome").eq("id", str(t_b)).execute()
            if res_b.data: nome_b = res_b.data[0]["nome"]
    except Exception as e:
        print(f"Erro ao buscar nomes: {e}")
    return nome_a, nome_b

# --- ESTADO E PLACAR DA BATALHA ---
def obter_estado_batalha(batalha_id):
    if not eh_uuid_valido(batalha_id): return None
    try:
        res = supabase.table("batalhas").select("*").eq("id", str(batalha_id)).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"Erro ao obter estado da batalha: {e}")
        return None

def calcular_placar_atual(batalha_id, t_a, t_b):
    if not eh_uuid_valido(batalha_id): return 0, 0
    try:
        res = supabase.table("batalha_respostas").select("time_id, resposta_correta").eq("batalha_id", str(batalha_id)).eq("resposta_correta", True).execute()
        pa = sum(1 for r in res.data if str(r["time_id"]) == str(t_a))
        pb = sum(1 for r in res.data if str(r["time_id"]) == str(t_b))
        return pa, pb
    except Exception as e:
        print(f"Erro ao calcular placar: {e}")
        return 0, 0

def obter_pergunta_atual(batalha_id, ordem):
    if not eh_uuid_valido(batalha_id): return None
    try:
        res_link = supabase.table("batalha_perguntas").select("questao_id").eq("batalha_id", str(batalha_id)).eq("ordem", int(ordem)).execute()
        if not res_link.data: return None
            
        q_id = res_link.data[0]["questao_id"]
        res_q = supabase.table("questoes").select("*").eq("id", q_id).execute()
        if not res_q.data: return None

        res_alt = supabase.table("alternativas").select("*").eq("questao_id", q_id).order("ordem").execute()
        
        pergunta = res_q.data[0]
        pergunta["alternativas"] = res_alt.data
        return pergunta
    except Exception as e:
        print(f"Erro ao buscar pergunta (Batalha {batalha_id}, Ordem {ordem}): {e}")
        return None

# --- CONTROLE DE FLUXO (INÍCIO, RESPOSTA E FIM) ---
def iniciar_partida_sincrona(batalha_id, time_inicial_id):
    if not eh_uuid_valido(batalha_id) or not eh_uuid_valido(time_inicial_id): return False
    try:
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
        supabase.table("batalhas").update({
            "status": "em_andamento",
            "time_da_vez_id": str(time_inicial_id),
            "pergunta_atual_ordem": 1,
            "status_sincrono": "aguardando_resposta",
            "inicio_turno": agora
        }).eq("id", str(batalha_id)).execute()
        return True
    except Exception as e:
        print(f"Erro ao iniciar: {e}")
        return False

def encerrar_partida_sincrona(batalha_id):
    if not eh_uuid_valido(batalha_id): return False
    try:
        supabase.table("batalhas").update({"status": "finalizada"}).eq("id", str(batalha_id)).execute()
        return True
    except: return False

def processar_passagem_de_vez(batalha_id, time_atual_id, time_adversario_id):
    """Executado quando o tempo de 45s esgota sem resposta."""
    if not eh_uuid_valido(batalha_id) or not eh_uuid_valido(time_adversario_id): return
    try:
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
        b = obter_estado_batalha(batalha_id)
        if not b: return
        
        ordem_atual = int(b.get("pergunta_atual_ordem", 1))
        
        if b.get("status_sincrono") == "rebate_ativo":
            # Se estourou o tempo no rebate, avança a questão
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": ordem_atual + 1,
                "status_sincrono": "aguardando_resposta",
                "time_da_vez_id": str(time_adversario_id),
                "inicio_turno": agora
            }).eq("id", str(batalha_id)).execute()
        else:
            # Se estourou na primeira tentativa, passa para o rebate
            supabase.table("batalhas").update({
                "status_sincrono": "rebate_ativo",
                "time_da_vez_id": str(time_adversario_id),
                "inicio_turno": agora
            }).eq("id", str(batalha_id)).execute()
    except Exception as e:
        print(f"Erro ao passar a vez: {e}")

def processar_resposta_sincrona(batalha_id, questao_id, time_id, alternativa_id, alternativa_correta, time_adversario_id, tentativa_atual):
    """O coração da batalha. Registra a resposta e avança o estado da arena."""
    try:
        # 1. Validação estrita de Foreign Keys
        if not eh_uuid_valido(time_id): return {"erro": "O aluno precisa estar em um time válido."}
        if not eh_uuid_valido(time_adversario_id): return {"erro": "A Equipe Adversária não está definida na arena."}
        
        b = obter_estado_batalha(batalha_id)
        if not b: return {"erro": "Batalha não encontrada."}
        ordem_atual = int(b.get("pergunta_atual_ordem", 1))

        # 2. Inserção na tabela batalha_respostas
        supabase.table("batalha_respostas").insert({
            "batalha_id": str(batalha_id),
            "questao_id": str(questao_id),
            "time_id": str(time_id),
            "alternativa_id": str(alternativa_id),
            "resposta_correta": bool(alternativa_correta),
            "tentativa_numero": int(tentativa_atual)
        }).execute()

        # 3. Lógica de Máquina de Estados (Avanço da Rodada)
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        if alternativa_correta:
            # Acertou: Avança a questão imediatamente
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": ordem_atual + 1,
                "time_da_vez_id": str(time_adversario_id),
                "status_sincrono": "aguardando_resposta",
                "inicio_turno": agora
            }).eq("id", str(batalha_id)).execute()
            return "acertou"
        else:
            if int(tentativa_atual) == 1:
                # Errou na 1ª tentativa: Vai para o rebate
                supabase.table("batalhas").update({
                    "status_sincrono": "rebate_ativo",
                    "time_da_vez_id": str(time_adversario_id),
                    "inicio_turno": agora
                }).eq("id", str(batalha_id)).execute()
                return "rebate"
            else:
                # Errou no rebate: Avança a questão
                supabase.table("batalhas").update({
                    "pergunta_atual_ordem": ordem_atual + 1,
                    "status_sincrono": "aguardando_resposta",
                    "time_da_vez_id": str(time_adversario_id),
                    "inicio_turno": agora
                }).eq("id", str(batalha_id)).execute()
                return "ambos_erraram"

    except Exception as e:
        return {"erro": f"Erro crítico no processamento: {str(e)}"}
    
# --- GERENCIAMENTO GERAL DE BATALHAS (Adicionado para a tela principal) ---

def listar_batalhas_ativas():
    """Busca todas as batalhas que estão agendadas ou em andamento."""
    try:
        # Busca ordenando pelas mais recentes
        resposta = supabase.table("batalhas").select("*").in_("status", ["agendada", "em_andamento"]).order("created_at", descending=True).execute()
        return resposta.data or []
    except Exception as e:
        print(f"Erro [listar_batalhas_ativas]: {e}")
        return []

def listar_historico_batalhas():
    """Busca batalhas já finalizadas para a aba de histórico."""
    try:
        resposta = supabase.table("batalhas").select("*").eq("status", "finalizada").order("created_at", descending=True).execute()
        return resposta.data or []
    except Exception as e:
        print(f"Erro [listar_historico_batalhas]: {e}")
        return []

def deletar_batalha(batalha_id):
    """Deleta a batalha e seus vínculos em cascata para evitar erro de Foreign Key."""
    if not eh_uuid_valido(batalha_id): return False
    try:
        b_id = str(batalha_id)
        # 1. Deleta respostas
        supabase.table("batalha_respostas").delete().eq("batalha_id", b_id).execute()
        
        # 2. Deleta alternativas vinculadas às questões da batalha
        perguntas = supabase.table("batalha_perguntas").select("questao_id").eq("batalha_id", b_id).execute()
        for p in perguntas.data:
            supabase.table("alternativas").delete().eq("questao_id", p['questao_id']).execute()
            
        # 3. Deleta o vínculo das questões
        supabase.table("batalha_perguntas").delete().eq("batalha_id", b_id).execute()
        
        # 4. Deleta a batalha principal
        supabase.table("batalhas").delete().eq("id", b_id).execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar batalha: {e}")
        return False