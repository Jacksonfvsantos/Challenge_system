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
        res = supabase.table("historico_batalhas").select("*").order("encerrado_em", descending=True).execute()
        return res.data or []
    except Exception:
        return []

def cadastrar_nova_batalha(titulo, descricao, modalidade, data_limite=None, lista_questoes_ids=None, time_a_id=None, time_b_id=None):
    try:
        payload = {
            "titulo": titulo.strip(),
            "descricao": descricao.strip() if descricao else None,
            "modalidade": modalidade,
            "finalizada": False,
            "pergunta_atual_ordem": 1,
            "status": "em_andamento" if modalidade == "assincrona" else "agendada",
            "status_sincrono": "aguardando_resposta" if modalidade == "sincrona" else None,
            "time_a_id": time_a_id,
            "time_b_id": time_b_id
        }
        res_batalha = supabase.table("batalhas").insert(payload).execute()
        if not res_batalha.data:
            return {"sucesso": False, "mensagem": "Falha ao instanciar batalha."}
            
        b_id = res_batalha.data[0]["id"]
        if lista_questoes_ids:
            linhas = [{"batalha_id": b_id, "questao_id": q_id, "ordem": i+1} for i, q_id in enumerate(lista_questoes_ids)]
            supabase.table("batalha_perguntas").insert(linhas).execute()
            
        return {"sucesso": True, "mensagem": "🚀 Competição publicada e QR Code gerado com sucesso!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def cadastrar_questao_rapida(enunciado, alternativas_texto, indice_correta):
    try:
        res_q = supabase.table("questoes").insert({"enunciado": enunciado.strip()}).execute()
        q_id = res_q.data[0]["id"]
        linhas = [{"questao_id": q_id, "texto": txt.strip(), "ordem": i+1, "correta": (i == indice_correta)} for i, txt in enumerate(alternativas_texto)]
        supabase.table("alternativas").insert(linhas).execute()
        return {"sucesso": True, "mensagem": "Questão salva!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def iniciar_partida_sincrona(batalha_id, time_inicial_id):
    try:
        supabase.table("batalhas").update({"status": "em_andamento", "time_da_vez_id": time_inicial_id, "status_sincrono": "aguardando_resposta", "pergunta_atual_ordem": 1}).eq("id", batalha_id).execute()
        return True
    except Exception:
        return False

def processar_resposta_sincrona(batalha_id, questao_id, time_id, alternativa_id, alternativa_correta, time_adversario_id, tentativa_atual):
    try:
        supabase.table("batalha_respostas").insert({"batalha_id": batalha_id, "questao_id": questao_id, "time_id": time_id, "alternativa_id": alternativa_id, "resposta_correta": bool(alternativa_correta), "tentativa_numero": int(tentativa_atual)}).execute()
        batalha = obter_estado_batalha(batalha_id)
        prox = int(batalha["pergunta_atual_ordem"]) + 1

        if alternativa_correta:
            supabase.table("batalhas").update({"pergunta_atual_ordem": prox, "status_sincrono": "aguardando_resposta", "time_da_vez_id": time_adversario_id}).eq("id", batalha_id).execute()
            return "acertou"
        else:
            if int(tentativa_atual) == 1:
                supabase.table("batalhas").update({"status_sincrono": "rebate_ativo", "time_da_vez_id": time_adversario_id}).eq("id", batalha_id).execute()
                return "rebate"
            else:
                supabase.table("batalhas").update({"pergunta_atual_ordem": prox, "status_sincrono": "aguardando_resposta", "time_da_vez_id": time_id}).eq("id", batalha_id).execute()
                return "ambos_erraram"
    except Exception:
        return "erro"

def encerrar_partida_sincrona(batalha_id):
    try:
        res_b = supabase.table("batalhas").select("*").eq("id", (b_id := batalha_id)).execute()
        if not res_b.data: return False
        b = res_b.data[0]
        
        t_a, t_b = b.get("time_a_id"), b.get("time_b_id")
        nome_a, nome_b = "Time A", "Time B"
        if t_a and t_b:
            rt = supabase.table("times").select("id, nome").in_("id", [t_a, t_b]).execute()
            if rt.data:
                mapa = {str(x["id"]).strip(): x["nome"] for x in rt.data}
                nome_a, nome_b = mapa.get(str(t_a).strip(), "Time A"), mapa.get(str(t_b).strip(), "Time B")

        resp = supabase.table("batalha_respostas").select("time_id, resposta_correta").eq("batalha_id", b_id).execute()
        p_a, p_b = 0, 0
        if resp.data:
            for r in resp.data:
                if r.get("resposta_correta") is True:
                    if str(r.get("time_id")).strip() == str(t_a).strip(): p_a += 1
                    elif str(r.get("time_id")).strip() == str(t_b).strip(): p_b += 1

        if p_a > p_b: desfecho = f"🥇 Vencedor: {nome_a} ({p_a} XP) | 🥈 Perdedor: {nome_b} ({p_b} XP)"
        elif p_b > p_a: desfecho = f"🥇 Vencedor: {nome_b} ({p_b} XP) | 🥈 Perdedor: {nome_a} ({p_a} XP)"
        else: desfecho = f"🤝 Resultado: Empate entre as equipes ({p_a} XP cada)"

        supabase.table("historico_batalhas").insert({
            "batalha_id": b_id, "titulo": b.get("titulo", "Arena"),
            "time_a_nome": nome_a, "time_b_nome": nome_b,
            "points_time_a": p_a, "points_time_b": p_b,
            "resultado_extenso": desfecho
        }).execute()

        supabase.table("batalhas").update({"finalizada": True, "status": "finalizada"}).eq("id", b_id).execute()
        return True
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")
        return False

def deletar_batalha(batalha_id):
    try:
        supabase.table("batalha_perguntas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalha_respostas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalhas").delete().eq("id", batalha_id).execute()
        return True
    except Exception:
        return False