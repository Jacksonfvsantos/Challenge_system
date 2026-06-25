import datetime
from database.conexao import supabase

def cadastrar_nova_batalha(titulo, descricao, modalidade, data_limite=None, lista_questoes_ids=None, time_a_id=None, time_b_id=None):
    """
    Registra uma nova competição no Supabase e vincula as questões selecionadas na tabela batalha_perguntas.
    """
    try:
        # 1. Prepara o payload da batalha principal
        payload = {
            "titulo": titulo,
            "descricao": descricao,
            "modalidade": modalidade,
            "finalizada": False,
            "pergunta_atual_ordem": 1,
            "status": "em_andamento" if modalidade == "assincrona" else "agendada",
            "status_sincrono": "aguardando_resposta" if modalidade == "sincrona" else None
        }

        if modalidade == "assincrona" and data_limite:
            # Garante formato ISO com fuso horário
            if isinstance(data_limite, datetime.datetime):
                payload["data_limite"] = data_limite.isoformat()
            else:
                payload["data_limite"] = str(data_limite)
        
        if modalidade == "sincrona":
            payload["time_a_id"] = time_a_id
            payload["time_b_id"] = time_b_id
            # O professor define o time da vez ao clicar em iniciar, entra como None por enquanto
            payload["time_da_vez_id"] = None

        # 2. Insere na tabela 'batalhas'
        res_batalha = supabase.table("batalhas").insert(payload).execute()
        
        if not res_batalha.data:
            return {"sucesso": False, "mensagem": "❌ Falha ao criar o registro da batalha."}
            
        nova_batalha_id = res_batalha.data[0]["id"]

        # 3. CRUCIAL: Vincula as questões na tabela intermediária 'batalha_perguntas'
        if modalidade == "sincrona" and lista_questoes_ids:
            linhas_vinculo = []
            for i, q_id in enumerate(lista_questoes_ids):
                linhas_vinculo.append({
                    "batalha_id": nova_batalha_id,
                    "questao_id": q_id,
                    "ordem": i + 1  # Round 1, Round 2, etc.
                })
            
            # Executa o insert em lote no Supabase
            if linhas_vinculo:
                supabase.table("batalha_perguntas").insert(linhas_vinculo).execute()

        return {"sucesso": True, "mensagem": "🚀 Competição publicada e questões vinculadas com sucesso!"}

    except Exception as e:
        print(f"❌ Erro em [cadastrar_nova_batalha]: {e}")
        return {"sucesso": False, "mensagem": f"Erro interno: {str(e)}"}

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

def encerrar_partida_sincrona(batalha_id):
    try:
        supabase.table("batalhas").update({"finalizada": True, "status": "finalizada"}).eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao encerrar partida: {e}")
        return False

def deletar_batalha(batalha_id):
    try:
        # Deleta vínculos primeiro por causa de Foreign Keys (se não houver ON DELETE CASCADE)
        supabase.table("batalha_perguntas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalha_respostas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalhas").delete().eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao deletar batalha: {e}")
        return False

def obter_batalhas_finalizadas():
    try:
        res = supabase.table("batalhas").select("*, time_a:time_a_id(nome), time_b:time_b_id(nome)").eq("finalizada", True).execute()
        return res.data or []
    except Exception:
        return []

def cadastrar_questao_rapida(enunciado, alternativas_texto, indice_correta):
    try:
        # Insere a questão
        res_q = supabase.table("questoes").insert({
            "enunciado": enunciado,
            "indice_correto": indice_correta
        }).execute()
        
        if not res_q.data:
            return {"sucesso": False, "mensagem": "Erro ao criar enunciado."}
            
        q_id = res_q.data[0]["id"]
        
        # Insere as alternativas correspondentes
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