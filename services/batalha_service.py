import datetime
from database.conexao import supabase

# ============================================================================
# 1. GERENCIAMENTO DE TIMES & EQUIPES
# ============================================================================

def criar_time(nome: str) -> bool:
    if not nome or not nome.strip():
        return False
    try:
        payload = {"nome": nome.strip()}
        resposta = supabase.table("times").insert(payload).execute()
        return bool(resposta.data and len(resposta.data) > 0)
    except Exception as erro:
        print(f"❌ Erro [criar_time]: {erro}")
        return False

def listar_times():
    try:
        resposta = supabase.table("times").select("*").order("nome").execute()
        return resposta.data or []
    except Exception as erro:
        print(f"❌ Erro [listar_times]: {erro}")
        return []

def editar_time(time_id: str, novo_nome: str) -> bool:
    if not str(time_id).strip() or not novo_nome or not novo_nome.strip():
        return False
    try:
        resposta = supabase.table("times").update({"nome": novo_nome.strip()}).eq("id", str(time_id).strip()).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [editar_time]: {erro}")
        return False

def deletar_time(time_id: str) -> bool:
    if not str(time_id).strip():
        return False
    try:
        resposta = supabase.table("times").delete().eq("id", str(time_id).strip()).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [deletar_time]: {erro}")
        return False

# ============================================================================
# 2. VÍNCULOS E GESTÃO DE INTEGRANTES (ALUNOS)
# ============================================================================

def aluno_tem_time(usuario_id: str) -> bool:
    if not str(usuario_id).strip():
        return False
    try:
        resposta = supabase.table("time_membros").select("id").eq("usuario_id", str(usuario_id).strip()).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [aluno_tem_time]: {erro}")
        return False

def entrar_no_time(time_id: str, usuario_id: str) -> bool:
    if not str(time_id).strip() or not str(usuario_id).strip():
        return False
    if aluno_tem_time(usuario_id):
        return False
    try:
        payload = {"time_id": str(time_id).strip(), "usuario_id": str(usuario_id).strip()}
        resposta = supabase.table("time_membros").insert(payload).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [entrar_no_time]: {erro}")
        return False

def listar_membros_time(time_id: str):
    if not str(time_id).strip():
        return []
    try:
        resposta = supabase.table("time_membros").select("usuario_id, usuarios(id, nome, email)").eq("time_id", str(time_id).strip()).execute()
        membros = []
        if resposta.data:
            for item in resposta.data:
                user_data = item.get("usuarios")
                if isinstance(user_data, dict):
                    membros.append({"id": user_data.get("id"), "nome": user_data.get("nome"), "email": user_data.get("email")})
        return membros
    except Exception as erro:
        print(f"❌ Erro [listar_membros_time]: {erro}")
        return []

def listar_alunos():
    try:
        resposta = supabase.table("usuarios").select("id, nome, email").eq("tipo_usuario", "aluno").order("nome").execute()
        return resposta.data or []
    except Exception as erro:
        print(f"❌ Erro [listar_alunos]: {erro}")
        return []

def adicionar_aluno(time_id: str, usuario_id: str) -> bool:
    return entrar_no_time(time_id, usuario_id)

def remover_aluno(time_id: str, usuario_id: str) -> bool:
    if not str(time_id).strip() or not str(usuario_id).strip():
        return False
    try:
        resposta = supabase.table("time_membros").delete().eq("time_id", str(time_id).strip()).eq("usuario_id", str(usuario_id).strip()).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [remover_aluno]: {erro}")
        return False

def blackjack_mover_aluno(usuario_id: str, destino_time_id: str) -> bool:
    if not str(usuario_id).strip() or not str(destino_time_id).strip():
        return False
    try:
        supabase.table("time_membros").delete().eq("usuario_id", str(usuario_id).strip()).execute()
        payload = {"time_id": str(destino_time_id).strip(), "usuario_id": str(usuario_id).strip()}
        resposta = supabase.table("time_membros").insert(payload).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [mover_aluno]: {erro}")
        return False

# Adiciona o alias para compatibilidade com as telas que buscam por mover_aluno
mover_aluno = blackjack_mover_aluno

# ============================================================================
# 3. MOTOR ATIVO DE PARTIDAS & CONTROLE DE TURNOS (BATE-REBATE)
# ============================================================================

def listar_batalhas():
    try:
        resposta = supabase.table("batalhas").select("*").order("created_at", descending=True).execute()
        return resposta.data or []
    except Exception as erro:
        print(f"❌ Erro [listar_batalhas]: {erro}")
        return []

def obter_estado_batalha(batalha_id):
    try:
        res = supabase.table("batalhas").select("*").eq("id", batalha_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"❌ Erro [obter_estado_batalha]: {e}")
        return None

def obter_batalhas_finalizadas():
    try:
        res = supabase.table("batalhas").select("*").eq("finalizada", True).order("created_at", descending=True).execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Erro [obter_batalhas_finalizadas]: {e}")
        return []

# 🚀 REINTRODUZIDO: Função exigida pelas telas de gerenciamento docente
def cadastrar_nova_batalha(titulo, descricao, modalidade, data_limite=None, lista_questoes_ids=None, time_a_id=None, time_b_id=None):
    try:
        payload = {
            "titulo": titulo.strip(),
            "descricao": descricao.strip() if descricao else None,
            "modalidade": modalidade,
            "finalizada": False,
            "pergunta_atual_ordem": 1,
            "status": "em_andamento" if modalidade == "assincrona" else "agendada",
            "status_sincrono": "aguardando_resposta" if modalidade == "sincrona" else None
        }

        if modalidade == "assincrona" and data_limite:
            payload["data_limite"] = data_limite.isoformat() if hasattr(data_limite, "isoformat") else str(data_limite)
        
        if modalidade == "sincrona":
            payload["time_a_id"] = time_a_id
            payload["time_b_id"] = time_b_id

        res_batalha = supabase.table("batalhas").insert(payload).execute()
        if not res_batalha.data:
            return {"sucesso": False, "mensagem": "❌ Falha ao criar o registro da batalha."}
            
        nova_batalha_id = res_batalha.data[0]["id"]

        if modalidade == "sincrona" and lista_questoes_ids:
            linhas_vinculo = []
            for i, q_id in enumerate(lista_questoes_ids):
                linhas_vinculo.append({
                    "batalha_id": nova_batalha_id,
                    "questao_id": q_id,
                    "ordem": i + 1
                })
            if linhas_vinculo:
                supabase.table("batalha_perguntas").insert(linhas_vinculo).execute()

        return {"sucesso": True, "mensagem": "🚀 Competição publicada e questões vinculadas com sucesso!"}
    except Exception as e:
        print(f"❌ Erro em [cadastrar_nova_batalha]: {e}")
        return {"sucesso": False, "mensagem": f"Erro interno: {str(e)}"}

def cadastrar_questao_rapida(enunciado, alternativas_texto, indice_correta):
    try:
        res_q = supabase.table("questoes").insert({
            "enunciado": enunciado,
            "tipo": "multipla_escolha",
            "pontos": 1
        }).execute()
        if not res_q.data:
            return {"sucesso": False, "mensagem": "Erro ao criar enunciado."}
            
        q_id = res_q.data[0]["id"]
        linhas_alt = []
        for i, texto in enumerate(alternativas_texto):
            linhas_alt.append({
                "questao_id": q_id,
                "texto": texto,
                "ordem": i + 1,
                "correta": (i == indice_correta)
            })
        supabase.table("alternativas").insert(linhas_alt).execute()
        return {"sucesso": True, "mensagem": "Questão e alternativas salvas com sucesso!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def iniciar_partida_sincrona(batalha_id, time_inicial_id):
    try:
        supabase.table("batalhas").update({
            "status": "em_andamento",
            "time_da_vez_id": time_inicial_id,
            "status_sincrono": "aguardando_resposta",
            "pergunta_atual_ordem": 1
        }).eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao iniciar partida: {e}")
        return False

def processar_resposta_sincrona(batalha_id, questao_id, time_id, alternativa_id, alternativa_correta, time_adversario_id, tentativa_atual):
    try:
        supabase.table("batalha_respostas").insert({
            "batalha_id": batalha_id,
            "questao_id": questao_id,
            "time_id": time_id,
            "alternativa_id": alternativa_id,
            "resposta_correta": bool(alternativa_correta),
            "tentativa_numero": int(tentativa_atual)
        }).execute()

        batalha = obter_estado_batalha(batalha_id)
        proxima_ordem = int(batalha["pergunta_atual_ordem"]) + 1

        if alternativa_correta:
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": proxima_ordem,
                "status_sincrono": "aguardando_resposta",
                "time_da_vez_id": time_adversario_id
            }).eq("id", batalha_id).execute()
            return "acertou"
        else:
            if int(tentativa_atual) == 1:
                supabase.table("batalhas").update({
                    "status_sincrono": "rebate_ativo",
                    "time_da_vez_id": time_adversario_id
                }).eq("id", batalha_id).execute()
                return "rebate"
            else:
                supabase.table("batalhas").update({
                    "pergunta_atual_ordem": proxima_ordem,
                    "status_sincrono": "aguardando_resposta",
                    "time_da_vez_id": time_id  
                }).eq("id", batalha_id).execute()
                return "ambos_erraram"
                
    except Exception as e:
        print(f"❌ Erro [processar_resposta_sincrona]: {e}")
        return "erro"

def verificar_paridade_rodada(batalha_id, numero_rodada):
    return True

def encerrar_partida_sincrona(batalha_id):
    try:
        supabase.table("batalhas").update({"finalizada": True, "status": "finalizada"}).eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao encerrar partida: {e}")
        return False

def deletar_batalha(batalha_id):
    try:
        supabase.table("batalha_perguntas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalha_respostas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalhas").delete().eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao deletar batalha: {e}")
        return False