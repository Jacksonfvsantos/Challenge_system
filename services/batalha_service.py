import datetime
from database.conexao import supabase

def eh_uuid_valido(valor):
    """Verifica se o ID não é vazio ou a string literal 'None'"""
    if not valor or str(valor).strip().lower() == "none" or str(valor).strip() == "":
        return False
    return True

# =====================================================================
# --- GERENCIAMENTO DE TIMES E ALUNOS
# =====================================================================
def criar_time(nome: str, usuario_id: str) -> bool:
    if not nome or not nome.strip() or not eh_uuid_valido(usuario_id): return False
    try:
        if aluno_tem_time(usuario_id): 
            return False
        
        resposta = supabase.table("times").insert({"nome": nome.strip()}).execute()
        if not resposta.data: return False
        
        time_id = resposta.data[0]["id"]
        
        supabase.table("time_membros").insert({
            "time_id": time_id,
            "usuario_id": str(usuario_id).strip(),
            "papel": "capitao",
            "status": "aceito"
        }).execute()
        
        return True
    except Exception as erro:
        print(f"Erro [criar_time]: {erro}")
        return False
    
def aceitar_membro(usuario_id: str) -> bool:
    """Muda o status do membro de pendente para aceito."""
    if not eh_uuid_valido(usuario_id): return False
    try:
        supabase.table("time_membros").update({"status": "aceito"}).eq("usuario_id", str(usuario_id).strip()).execute()
        return True
    except Exception as e:
        print(f"Erro [aceitar_membro]: {e}")
        return False

def listar_times():
    try:
        resposta = supabase.table("times").select("*").order("nome").execute()
        return resposta.data or []
    except Exception as erro:
        print(f"Erro [listar_times]: {erro}")
        return []

def deletar_time(time_id: str) -> bool:
    if not eh_uuid_valido(time_id): return False
    try:
        supabase.table("time_membros").delete().eq("time_id", str(time_id).strip()).execute()
        supabase.table("times").delete().eq("id", str(time_id).strip()).execute()
        return True
    except Exception as e:
        print(f"Erro [deletar_time]: {e}")
        return False

def aluno_tem_time(usuario_id: str) -> bool:
    if not eh_uuid_valido(usuario_id): return False
    try:
        resposta = supabase.table("time_membros").select("id").eq("usuario_id", str(usuario_id).strip()).execute()
        return len(resposta.data) > 0
    except Exception: return False

def entrar_no_time(time_id: str, usuario_id: str) -> bool:
    if not eh_uuid_valido(time_id) or not eh_uuid_valido(usuario_id): return False
    if aluno_tem_time(usuario_id): return False
    try:
        supabase.table("time_membros").insert({"time_id": str(time_id).strip(), "usuario_id": str(usuario_id).strip()}).execute()
        return True
    except Exception: return False

def adicionar_aluno(time_id: str, usuario_id: str) -> bool:
    return entrar_no_time(time_id, usuario_id)

def listar_membros_time(time_id: str):
    if not eh_uuid_valido(time_id): return []
    try:
        resposta = supabase.table("time_membros").select("usuario_id, usuarios(id, nome, email)")\
            .eq("time_id", str(time_id).strip())\
            .eq("status", "aceito").execute()
        
        membros = []
        if resposta.data:
            for item in resposta.data:
                user_data = item.get("usuarios")
                if isinstance(user_data, dict):
                    membros.append({"id": user_data.get("id"), "nome": user_data.get("nome"), "email": user_data.get("email")})
        return membros
    except Exception as e:
        print(f"Erro [listar_membros_time]: {e}")
        return []
    
def mover_aluno(usuario_id: str, novo_time_id: str) -> bool:
    if not eh_uuid_valido(usuario_id) or not eh_uuid_valido(novo_time_id): return False
    try:
        supabase.table("time_membros").delete().eq("usuario_id", str(usuario_id).strip()).execute()
        supabase.table("time_membros").insert({"time_id": str(novo_time_id).strip(), "usuario_id": str(usuario_id).strip()}).execute()
        return True
    except Exception as e:
        print(f"Erro [mover_aluno]: {e}")
        return False

def remover_aluno(usuario_id: str) -> bool:
    if not eh_uuid_valido(usuario_id): return False
    try:
        supabase.table("time_membros").delete().eq("usuario_id", str(usuario_id).strip()).execute()
        return True
    except Exception as e:
        print(f"Erro [remover_aluno]: {e}")
        return False

def listar_alunos():
    try:
        resposta = supabase.table("usuarios").select("id, nome, email").eq("tipo_usuario", "aluno").order("nome").execute()
        return resposta.data or []
    except Exception: return []

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
    except Exception as e: print(f"Erro ao buscar nomes: {e}")
    return nome_a, nome_b

def verificar_capitao(usuario_id: str) -> bool:
    """Verifica se o usuário logado possui o papel de capitão na sua equipe."""
    try:
        res = supabase.table("time_membros").select("papel").eq("usuario_id", str(usuario_id).strip()).execute()
        if res.data and res.data[0].get("papel") == "capitao":
            return True
        return False
    except Exception: return False

def listar_membros_pendentes(time_id: str):
    """Retorna apenas os alunos que solicitaram entrada e estão com status pendente."""
    try:
        res = supabase.table("time_membros").select("usuario_id, usuarios(id, nome, email)")\
            .eq("time_id", str(time_id).strip()).eq("status", "pendente").execute()
        membros = []
        if res.data:
            for item in res.data:
                user_data = item.get("usuarios")
                if isinstance(user_data, dict):
                    membros.append({"id": user_data.get("id"), "nome": user_data.get("nome"), "email": user_data.get("email")})
        return membros
    except Exception: return []

def obter_status_membro(usuario_id: str) -> str:
    """
    Retorna o status atual do aluno na equipe ('aceito', 'pendente').
    Retorna None se ele não estiver vinculado a nenhuma equipe.
    """
    if not eh_uuid_valido(usuario_id): return None
    try:
        res = supabase.table("time_membros").select("status").eq("usuario_id", str(usuario_id).strip()).execute()
        if res.data:
            return res.data[0].get("status")
        return None
    except Exception as e:
        print(f"Erro [obter_status_membro]: {e}")
        return None
    
def recusar_membro(usuario_id: str) -> bool:
    """Deleta o vínculo do aluno com a equipe (recusa a entrada ou remove do time)."""
    if not eh_uuid_valido(usuario_id): return False
    try:
        supabase.table("time_membros").delete().eq("usuario_id", str(usuario_id).strip()).execute()
        return True
    except Exception as e:
        print(f"Erro [recusar_membro]: {e}")
        return False

# =====================================================================
# --- GERENCIAMENTO GERAL DE BATALHAS E PLACAR
# =====================================================================
def cadastrar_nova_batalha(titulo, descricao, time_a_id=None, time_b_id=None, modalidade="sincrona"):
    try:
        # Monta o payload base apenas com os campos que não são Chaves Estrangeiras (UUIDs)
        payload = {
            "titulo": titulo.strip(),
            "descricao": descricao.strip() if descricao else None,
            "modalidade": modalidade,
            "status": "agendada",
            "finalizada": False,
            "pergunta_atual_ordem": 1
        }
        if time_a_id and str(time_a_id).strip() != "None": 
            payload["time_a_id"] = str(time_a_id).strip()
        if time_b_id and str(time_b_id).strip() != "None": 
            payload["time_b_id"] = str(time_b_id).strip()
            
        res = supabase.table("batalhas").insert(payload).execute()
        return {"sucesso": True, "data": res.data}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def listar_batalhas_ativas():
    try:
        res = supabase.table("batalhas")\
            .select("*")\
            .neq("status", "finalizada")\
            .order("created_at", desc=True)\
            .execute()
        return res.data or []
    except Exception as e:
        print(f"Erro ao listar batalhas ativas: {e}")
        return []

def listar_historico_batalhas():
    try:
        resposta = supabase.table("historico_batalhas").select("*").order("encerrado_em", desc=True).execute()
        return resposta.data or []
    except Exception as e:
        print(f"Erro [listar_historico_batalhas]: {e}")
        return []

def deletar_batalha(batalha_id):
    if not eh_uuid_valido(batalha_id): return False
    try:
        b_id = str(batalha_id)
        
        # 1. Limpa o registro do placar final na tabela de histórico
        supabase.table("historico_batalhas").delete().eq("batalha_id", b_id).execute()
        
        # 2. Limpa as respostas dos alunos
        supabase.table("batalha_respostas").delete().eq("batalha_id", b_id).execute()
        
        # 3. Limpa as questões e alternativas vinculadas
        perguntas = supabase.table("batalha_perguntas").select("questao_id").eq("batalha_id", b_id).execute()
        for p in perguntas.data:
            supabase.table("alternativas").delete().eq("questao_id", p['questao_id']).execute()
            
        supabase.table("batalha_perguntas").delete().eq("batalha_id", b_id).execute()
        
        # 4. Deleta a arena principal
        supabase.table("batalhas").delete().eq("id", b_id).execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar batalha: {e}")
        return False

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
    
def obter_batalhas_finalizadas():
    """Busca batalhas finalizadas e mescla com seus resultados do histórico."""
    try:
        # 1. Traz as batalhas (para sabermos a modalidade e título)
        res_batalhas = supabase.table("batalhas").select("*").eq("status", "finalizada").order("created_at", desc=True).execute()
        batalhas = res_batalhas.data or []
        
        # 2. Traz os resultados salvos
        res_hist = supabase.table("historico_batalhas").select("*").execute()
        mapa_historico = {str(h["batalha_id"]): h for h in (res_hist.data or [])}
        
        # 3. Mescla tudo em uma lista só
        lista_completa = []
        for b in batalhas:
            b_id = str(b["id"])
            hist = mapa_historico.get(b_id, {})
            
            # Injeta os dados do histórico para dentro do dicionário da batalha
            b["resultado_extenso"] = hist.get("resultado_extenso", "Resultado em processamento...")
            b["time_a_nome"] = hist.get("time_a_nome", "Equipe A")
            b["time_b_nome"] = hist.get("time_b_nome", "Equipe B")
            b["pontos_time_a"] = hist.get("pontos_time_a", 0)
            b["pontos_time_b"] = hist.get("pontos_time_b", 0)
            
            lista_completa.append(b)
            
        return lista_completa
    except Exception as e:
        print(f"Erro [obter_batalhas_finalizadas]: {e}")
        return []

# =====================================================================
# --- CADASTRO E BUSCA DE QUESTÕES DA BATALHA
# =====================================================================
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
        print(f"Erro ao buscar pergunta: {e}")
        return None
    
def obter_total_questoes(batalha_id):
    """Conta quantas questões existem vinculadas a esta batalha."""
    if not eh_uuid_valido(batalha_id): return 0
    try:
        res = supabase.table("batalha_perguntas").select("id", count='exact').eq("batalha_id", str(batalha_id)).execute()
        return res.count or 0
    except Exception: 
        return 0

def cadastrar_questao_rapida(batalha_id: str, enunciado: str, alternativas_lista: list, correta_idx: int) -> bool:
    if not eh_uuid_valido(batalha_id): return False
    try:
        b_id = str(batalha_id).strip()
        res_q = supabase.table("questoes").insert({"enunciado": str(enunciado).strip()}).execute()
        
        if not res_q.data: return False
        questao_id = res_q.data[0]["id"]
        
        payload_alternativas = []
        for i, texto_alt in enumerate(alternativas_lista):
            payload_alternativas.append({
                "questao_id": questao_id, "texto": str(texto_alt).strip(), "ordem": i + 1, "correta": (i == correta_idx)
            })
        supabase.table("alternativas").insert(payload_alternativas).execute()
        
        res_ordem = supabase.table("batalha_perguntas").select("ordem").eq("batalha_id", b_id).execute()
        proxima_ordem = len(res_ordem.data) + 1 if res_ordem.data else 1
        
        supabase.table("batalha_perguntas").insert({"batalha_id": b_id, "questao_id": questao_id, "ordem": proxima_ordem}).execute()
        return True
    except Exception as e:
        print(f"Erro [cadastrar_questao_rapida]: {e}")
        return False

def cadastrar_questoes_batalha(batalha_id, lista_questoes):
    if not eh_uuid_valido(batalha_id): return {"sucesso": False, "mensagem": "Batalha inválida."}
    try:
        for q in lista_questoes:
            cadastrar_questao_rapida(batalha_id, q["enunciado"], q["alternativas"], q["correta_idx"])
        return {"sucesso": True}
    except Exception as e: return {"sucesso": False, "mensagem": str(e)}

def salvar_questoes_lote_ia(batalha_id, lista_questoes):
    if not lista_questoes or not isinstance(lista_questoes, list): return {"sucesso": False, "mensagem": "Formato inválido."}
    return cadastrar_questoes_batalha(batalha_id, lista_questoes)

# =====================================================================
# --- MOTOR DO JOGO E CONTROLE DE FLUXO (RODADA SÍNCRONA)
# =====================================================================
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

def processar_passagem_de_vez(batalha_id, time_atual_id, time_adversario_id):
    if not eh_uuid_valido(batalha_id) or not eh_uuid_valido(time_adversario_id): return
    try:
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
        b = obter_estado_batalha(batalha_id)
        if not b: return
        ordem_atual = int(b.get("pergunta_atual_ordem", 1))
        
        if b.get("status_sincrono") == "rebate_ativo":
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": ordem_atual + 1, "status_sincrono": "aguardando_resposta",
                "time_da_vez_id": str(time_adversario_id), "inicio_turno": agora
            }).eq("id", str(batalha_id)).execute()
        else:
            supabase.table("batalhas").update({
                "status_sincrono": "rebate_ativo", "time_da_vez_id": str(time_adversario_id), "inicio_turno": agora
            }).eq("id", str(batalha_id)).execute()
    except Exception as e: print(f"Erro ao passar a vez: {e}")

def processar_resposta_sincrona(batalha_id, questao_id, time_id, alternativa_id, alternativa_correta, time_adversario_id, tentativa_atual):
    try:
        if not time_id or str(time_id) == "None":
            return "erro: time_id_invalido"
        
        # --- 1. TRAVA DE CONCORRÊNCIA (Impede múltiplos cliques do mesmo time) ---
        trava = supabase.table("batalha_respostas")\
            .select("id")\
            .eq("batalha_id", str(batalha_id))\
            .eq("questao_id", str(questao_id))\
            .eq("time_id", str(time_id))\
            .eq("tentativa_numero", int(tentativa_atual))\
            .execute()
            
        if trava.data:
            # Se já existir um registro, significa que outro membro da equipe já clicou
            return "ja_respondida"
        
        # --- 2. PROCESSAMENTO NORMAL ---
        batalha = obter_estado_batalha(batalha_id)
        ordem_atual = int(batalha.get("pergunta_atual_ordem", 1))
        total_q = obter_total_questoes(batalha_id) # Para encerrar o jogo automaticamente

        # Salva a resposta do aluno mais rápido
        supabase.table("batalha_respostas").insert({
            "batalha_id": str(batalha_id), "questao_id": str(questao_id), 
            "time_id": str(time_id), "alternativa_id": str(alternativa_id), 
            "resposta_correta": bool(alternativa_correta), "tentativa_numero": int(tentativa_atual)
        }).execute()

        agora = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if alternativa_correta:
            if ordem_atual >= total_q:
                encerrar_partida_sincrona(batalha_id)
                return "fim_de_jogo"
            else:
                supabase.table("batalhas").update({
                    "pergunta_atual_ordem": ordem_atual + 1,
                    "time_da_vez_id": str(time_adversario_id),
                    "status_sincrono": "aguardando_resposta",
                    "inicio_turno": agora
                }).eq("id", str(batalha_id)).execute()
                return "acertou"
        else:
            if int(tentativa_atual) == 1:
                supabase.table("batalhas").update({
                    "status_sincrono": "rebate_ativo", 
                    "time_da_vez_id": str(time_adversario_id),
                    "inicio_turno": agora
                }).eq("id", str(batalha_id)).execute()
                return "rebate"
            else:
                if ordem_atual >= total_q:
                    encerrar_partida_sincrona(batalha_id)
                    return "fim_de_jogo"
                else:
                    supabase.table("batalhas").update({
                        "pergunta_atual_ordem": ordem_atual + 1,
                        "status_sincrono": "aguardando_resposta",
                        "time_da_vez_id": str(time_adversario_id),
                        "inicio_turno": agora
                    }).eq("id", str(batalha_id)).execute()
                    return "ambos_erraram"
    except Exception as e:
        return f"erro: {str(e)}"

def encerrar_partida_sincrona(batalha_id):
    try:
        res_b = supabase.table("batalhas").select("*").eq("id", batalha_id).execute()
        if not res_b.data: return False
        b = res_b.data[0]
        
        t_a, t_b = b.get("time_a_id"), b.get("time_b_id")
        
        # 1. Busca os nomes reais e exatos das equipes no banco de dados
        nome_ta, nome_tb = obter_nomes_dos_times(t_a, t_b)
        
        resp = supabase.table("batalha_respostas").select("time_id, resposta_correta").eq("batalha_id", batalha_id).execute()
        p_a = sum(1 for r in resp.data if str(r.get("time_id")).strip() == str(t_a).strip() and r.get("resposta_correta"))
        p_b = sum(1 for r in resp.data if str(r.get("time_id")).strip() == str(t_b).strip() and r.get("resposta_correta"))

        # 2. Formata a mensagem de desfecho utilizando os nomes reais
        desfecho = f"Resultado final: {nome_ta} ({p_a}) vs {nome_tb} ({p_b})"
        
        # 3. Salva no histórico o nome de fato, e não mais a ID
        supabase.table("historico_batalhas").insert({
            "batalha_id": batalha_id, 
            "titulo": b.get("titulo"),
            "time_a_nome": nome_ta, 
            "time_b_nome": nome_tb,
            "pontos_time_a": p_a, 
            "pontos_time_b": p_b,
            "resultado_extenso": desfecho
        }).execute()

        supabase.table("batalhas").update({"status": "finalizada", "finalizada": True}).eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao encerrar: {e}")
        return False

def processar_resposta_assincrona(batalha_id, questao_id, time_id, alternativa_id, alternativa_correta):
    try:
        if not eh_uuid_valido(time_id): return "erro"
        
        res = supabase.table("batalha_respostas").select("id").eq("batalha_id", str(batalha_id)).eq("questao_id", str(questao_id)).eq("time_id", str(time_id)).execute()
        if res.data: return "ja_respondida"
        
        supabase.table("batalha_respostas").insert({
            "batalha_id": str(batalha_id), "questao_id": str(questao_id), 
            "time_id": str(time_id), "alternativa_id": str(alternativa_id), 
            "resposta_correta": bool(alternativa_correta), "tentativa_numero": 1
        }).execute()
        
        return "acertou" if alternativa_correta else "errou"
    except Exception as e:
        return f"erro: {str(e)}"