import datetime
from database.conexao import supabase

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

def aluno_tem_time(usuario_id: str) -> bool:
    try:
        resposta = supabase.table("time_membros").select("id").eq("usuario_id", str(usuario_id).strip()).execute()
        return len(resposta.data) > 0
    except Exception:
        return False

def entrar_no_time(time_id: str, usuario_id: str) -> bool:
    if aluno_tem_time(usuario_id):
        return False
    try:
        supabase.table("time_membros").insert({"time_id": str(time_id).strip(), "usuario_id": str(usuario_id).strip()}).execute()
        return True
    except Exception:
        return False

def listar_membros_time(time_id: str):
    try:
        resposta = supabase.table("time_membros").select("usuario_id, usuarios(id, nome, email)").eq("time_id", str(time_id).strip()).execute()
        membros = []
        if resposta.data:
            for item in resposta.data:
                user_data = item.get("usuarios")
                if isinstance(user_data, dict):
                    membros.append({"id": user_data.get("id"), "nome": user_data.get("nome"), "email": user_data.get("email")})
        return membros
    except Exception:
        return []

def listar_alunos():
    try:
        resposta = supabase.table("usuarios").select("id, nome, email").eq("tipo_usuario", "aluno").order("nome").execute()
        return resposta.data or []
    except Exception:
        return []

def adicionar_aluno(time_id: str, usuario_id: str) -> bool:
    return entrar_no_time(time_id, usuario_id)

def remover_aluno(time_id: str, usuario_id: str) -> bool:
    try:
        supabase.table("time_membros").delete().eq("time_id", str(time_id).strip()).eq("usuario_id", str(usuario_id).strip()).execute()
        return True
    except Exception:
        return False

def blackjack_mover_aluno(usuario_id: str, destino_time_id: str) -> bool:
    try:
        supabase.table("time_membros").delete().eq("usuario_id", str(usuario_id).strip()).execute()
        supabase.table("time_membros").insert({"time_id": str(destino_time_id).strip(), "usuario_id": str(usuario_id).strip()}).execute()
        return True
    except Exception:
        return False

mover_aluno = blackjack_mover_aluno

def obter_estado_batalha(batalha_id):
    try:
        res = supabase.table("batalhas").select("*").eq("id", batalha_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def obter_batalhas_finalizadas():
    try:
        res = supabase.table("historico_batalhas").select("*").order("encerrado_em", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def cadastrar_questoes_batalha(batalha_id, lista_questoes):
    """
    lista_questoes: Lista de dicts com 'enunciado', 'alternativas' (lista), 'correta_idx' (int)
    """
    try:
        for i, q in enumerate(lista_questoes):
            res_q = supabase.table("questoes").insert({
                "enunciado": q["enunciado"].strip()
            }).execute()
            
            if res_q.data:
                q_id = res_q.data[0]["id"]
                supabase.table("batalha_perguntas").insert({
                    "batalha_id": batalha_id,
                    "questao_id": q_id,
                    "ordem": i + 1
                }).execute()
                
                alternativas = [{"questao_id": q_id, "texto": txt, "ordem": idx+1, "correta": (idx == q["correta_idx"])} 
                               for idx, txt in enumerate(q["alternativas"])]
                supabase.table("alternativas").insert(alternativas).execute()
        return {"sucesso": True}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def cadastrar_questao_rapida(batalha_id, enunciado, alternativas_texto, indice_correta):
    try:
        res_q = supabase.table("questoes").insert({"enunciado": enunciado.strip()}).execute()
        q_id = res_q.data[0]["id"]
        
        res_contagem = supabase.table("batalha_perguntas").select("count", count='exact').eq("batalha_id", batalha_id).execute()
        proxima_ordem = (res_contagem.count or 0) + 1
        
        supabase.table("batalha_perguntas").insert({
            "batalha_id": batalha_id,
            "questao_id": q_id,
            "ordem": proxima_ordem
        }).execute()

        linhas = [{"questao_id": q_id, "texto": txt.strip(), "ordem": i+1, "correta": (i == indice_correta)} 
                 for i, txt in enumerate(alternativas_texto)]
        supabase.table("alternativas").insert(linhas).execute()
        
        return {"sucesso": True, "mensagem": "Questão salva e vinculada à batalha!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def iniciar_partida_sincrona(batalha_id, time_inicial_id):
    try:
        clean_time_id = str(time_inicial_id).strip()
        supabase.table("batalhas").update({
            "status": "em_andamento", 
            "time_da_vez_id": clean_time_id, 
            "status_sincrono": "aguardando_resposta", 
            "pergunta_atual_ordem": 1,
            "inicio_turno": datetime.datetime.now().isoformat() 
        }).eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"Erro ao iniciar: {e}")
        return False

def processar_resposta_sincrona(batalha_id, questao_id, time_id, alternativa_id, alternativa_correta, time_adversario_id, tentativa_atual):
    try:
        supabase.table("batalha_respostas").insert({
            "batalha_id": batalha_id, "questao_id": questao_id, 
            "time_id": time_id, "alternativa_id": alternativa_id, 
            "resposta_correta": bool(alternativa_correta), "tentativa_numero": int(tentativa_atual)
        }).execute()

        batalha = obter_estado_batalha(batalha_id)
        ordem_atual = int(batalha.get("pergunta_atual_ordem", 1))

        if alternativa_correta:
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": ordem_atual + 1,
                "time_da_vez_id": time_adversario_id,
                "status_sincrono": "aguardando_resposta",
                "inicio_turno": datetime.datetime.now(datetime.timezone.utc).isoformat()
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
                    "pergunta_atual_ordem": ordem_atual + 1,
                    "status_sincrono": "aguardando_resposta",
                    "time_da_vez_id": time_adversario_id,
                    "inicio_turno": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }).eq("id", batalha_id).execute()
                return "ambos_erraram"
    except Exception as e:
        return f"erro: {str(e)}"

def encerrar_partida_sincrona(batalha_id):
    try:
        res_b = supabase.table("batalhas").select("*").eq("id", batalha_id).execute()
        if not res_b.data: return False
        b = res_b.data[0]
        
        t_a, t_b = b.get("time_a_id"), b.get("time_b_id")
        resp = supabase.table("batalha_respostas").select("time_id, resposta_correta").eq("batalha_id", batalha_id).execute()
        p_a = sum(1 for r in resp.data if str(r.get("time_id")).strip() == str(t_a).strip() and r.get("resposta_correta"))
        p_b = sum(1 for r in resp.data if str(r.get("time_id")).strip() == str(t_b).strip() and r.get("resposta_correta"))

        desfecho = f"Resultado final: Time A {p_a} vs Time B {p_b}"
        supabase.table("historico_batalhas").insert({
            "batalha_id": batalha_id, 
            "titulo": b.get("titulo"),
            "time_a_nome": str(t_a), "time_b_nome": str(t_b),
            "pontos_time_a": p_a, "pontos_time_b": p_b,
            "resultado_extenso": desfecho
        }).execute()

        supabase.table("batalhas").update({"status": "finalizada", "finalizada": True}).eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao encerrar: {e}")
        return False

def deletar_batalha(batalha_id):
    try:
        supabase.table("batalha_perguntas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalha_respostas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalhas").delete().eq("id", batalha_id).execute()
        return True
    except Exception:
        return False

def listar_batalhas_ativas():
    try:
        res = supabase.table("batalhas")\
            .select("*, times:time_a_id(nome)")\
            .neq("status", "finalizada")\
            .order("created_at", desc=True)\
            .execute()
        return res.data or []
    except Exception as e:
        print(f"Erro ao listar: {e}")
        return []

def buscar_detalhes_prova_ou_batalha(batalha_id):
    try:
        res = supabase.table("batalhas").select("*").eq("id", batalha_id).single().execute()
        return res.data
    except Exception:
        return None
    
def listar_times():
    try:
        res = supabase.table("times").select("id, nome").execute()
        return res.data or []
    except Exception:
        return []
    
def processar_resposta_assincrona(batalha_id, questao_id, time_id, alternativa_id, alternativa_correta):
    try:
        supabase.table("batalha_respostas").insert({
            "batalha_id": batalha_id, "questao_id": questao_id, 
            "time_id": time_id, "alternativa_id": alternativa_id, 
            "resposta_correta": bool(alternativa_correta), "tentativa_numero": 1
        }).execute()
        return {"sucesso": True}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}
    
def cadastrar_nova_batalha(titulo, descricao, time_a_id, time_b_id=None, modalidade="sincrona"):
    try:
        payload = {
            "titulo": titulo.strip(),
            "descricao": descricao.strip() if descricao else None,
            "modalidade": modalidade,
            "status": "agendada",
            "time_a_id": time_a_id,
            "time_b_id": time_b_id,
            "finalizada": False,
            "pergunta_atual_ordem": 1
        }
        res = supabase.table("batalhas").insert(payload).execute()
        return {"sucesso": True, "data": res.data}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}
    
def obter_pergunta_atual(batalha_id, ordem):
    try:
        res_link = supabase.table("batalha_perguntas")\
            .select("questao_id")\
            .eq("batalha_id", batalha_id)\
            .eq("ordem", ordem)\
            .single().execute()
        
        if not res_link.data:
            return None
            
        q_id = res_link.data["questao_id"]
        
        res_q = supabase.table("questoes").select("*").eq("id", q_id).single().execute()
        
        res_alt = supabase.table("alternativas").select("*").eq("questao_id", q_id).order("ordem").execute()
        
        pergunta = res_q.data
        pergunta["alternativas"] = res_alt.data
        return pergunta
    except Exception as e:
        print(f"DEBUG - Erro ao buscar pergunta (Batalha {batalha_id}, Ordem {ordem}): {e}")
        return None
    
def obter_time_do_usuario(usuario_id):
    try:
        res = supabase.table("time_membros").select("time_id").eq("usuario_id", usuario_id).execute()
        return [item["time_id"] for item in res.data] if res.data else [None]
    except: return [None]

def calcular_placar_atual(batalha_id, t_a, t_b):
    try:
        res = supabase.table("batalha_respostas").select("time_id, resposta_correta").eq("batalha_id", batalha_id).eq("resposta_correta", True).execute()
        pa = sum(1 for r in res.data if str(r["time_id"]) == str(t_a))
        pb = sum(1 for r in res.data if str(r["time_id"]) == str(t_b))
        return pa, pb
    except: return 0, 0

def obter_nomes_dos_times(t_a, t_b):
    try:
        res = supabase.table("times").select("id, nome").in_("id", [t_a, t_b]).execute()
        mapa = {str(x["id"]): x["nome"] for x in res.data}
        return mapa.get(str(t_a), "Time A"), mapa.get(str(t_b), "Time B")
    except: return "Time A", "Time B"