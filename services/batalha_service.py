from database.conexao import supabase

# ============================================================================
# 1. GESTÃO DE EQUIPES E MEMBROS (PERFIL ALUNO)
# ============================================================================

def aluno_criar_e_entrar_no_time(nome_time, usuario_id):
    """Cria o time e vincula o aluno criador como primeiro membro automaticamente."""
    try:
        dados_time = {
            "nome": nome_time.strip()
        }
        
        res_time = supabase.table("times").insert(dados_time).execute()
        
        if not res_time.data:
            return {"sucesso": False, "mensagem": "Erro ao registrar o nome do time (o nome já pode estar em uso)."}
            
        time_id = res_time.data[0]["id"]
        
        res_membro = supabase.table("time_membros").insert({
            "time_id": time_id,
            "usuario_id": usuario_id
        }).execute()
        
        if res_membro.data:
            return {"sucesso": True, "mensagem": f"Equipe '{nome_time}' criada com sucesso!"}
            
        return {"sucesso": False, "mensagem": "Time criado, mas falha ao vincular seu perfil de estudante."}
    except Exception as e:
        print(f"❌ Erro operacional [aluno_criar_e_entrar_no_time]: {e}")
        return {"sucesso": False, "mensagem": f"Erro interno de comunicação com o servidor: {str(e)}"}


def aluno_sair_do_time(usuario_id):
    """Remove o vínculo do aluno com o seu time atual."""
    try:
        res = supabase.table("time_membros").delete().eq("usuario_id", usuario_id).execute()
        if res.data:
            return {"sucesso": True, "mensagem": "Você saiu da equipe com sucesso!"}
        return {"sucesso": False, "mensagem": "Você não possui um time ativo no momento."}
    except Exception as e:
        print(f"❌ Erro [aluno_sair_do_time]: {e}")
        return {"sucesso": False, "mensagem": "Erro ao processar desligamento."}


# ============================================================================
# 2. PROVISIONAMENTO DA ARENA HÍBRIDA (PERFIL PROFESSOR)
# ============================================================================

def cadastrar_nova_batalha(titulo, descricao, modalidade, data_limite=None, lista_questoes_ids=[], time_a_id=None, time_b_id=None):
    """Grava o cabeçalho da batalha vinculando as duas equipes escolhidas e as perguntas."""
    try:
        payload = {
            "titulo": titulo.strip(),
            "descricao": descricao.strip(),
            "modalidade": modalidade,
            "status": "agendada",
            "finalizada": False,
            "pergunta_atual_ordem": 1,
            "status_sincrono": "aguardando_resposta",
            "time_a_id": time_a_id,
            "time_b_id": time_b_id
        }
        
        if modalidade == "assincrona" and data_limite:
            payload["data_limite"] = data_limite.isoformat()

        res_batalha = supabase.table("batalhas").insert(payload).execute()
        
        if not res_batalha.data:
            return {"sucesso": False, "mensagem": "Erro ao criar registro principal da batalha."}
            
        batalha_id = res_batalha.data[0]["id"]

        if modalidade == "sincrona" and lista_questoes_ids:
            batch_perguntas = []
            for idx, q_id in enumerate(lista_questoes_ids, start=1):
                batch_perguntas.append({
                    "batalha_id": batalha_id,
                    "questao_id": q_id,
                    "ordem": idx
                })
            supabase.table("batalha_perguntas").insert(batch_perguntas).execute()

        return {"sucesso": True, "mensagem": f"Batalha '{titulo}' provisionada com sucesso!"}
    except Exception as e:
        print(f"❌ Erro [cadastrar_nova_batalha]: {e}")
        return {"sucesso": False, "mensagem": f"Erro operacional: {str(e)}"}


# ============================================================================
# 3. ORQUESTRAÇÃO SÍNCRONA DE ROUNDS & CICLO DE VIDA (NOVO)
# ============================================================================

def iniciar_partida_sincrona(batalha_id, primeiro_time_id):
    """Muda o status da batalha para em_andamento e define qual das duas equipes abre o primeiro turno."""
    try:
        res = supabase.table("batalhas").update({
            "status": "em_andamento",
            "status_sincrono": "aguardando_resposta",
            "pergunta_atual_ordem": 1,
            "time_da_vez_id": primeiro_time_id
        }).eq("id", batalha_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro [iniciar_partida_sincrona]: {e}")
        return False


def encerrar_partida_sincrona(batalha_id):
    """Força o encerramento manual da batalha, enviando-a para o arquivo de histórico."""
    try:
        res = supabase.table("batalhas").update({
            "status": "finalizada",
            "finalizada": True,
            "status_sincrono": "encerrado"
        }).eq("id", batalha_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro [encerrar_partida_sincrona]: {e}")
        return False


def deletar_batalha(batalha_id):
    """Apaga completamente os registros e históricos de uma batalha (limpeza de testes)."""
    try:
        # Limpa as tabelas filhas para evitar quebra de Foreign Keys
        supabase.table("batalha_perguntas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalha_respostas").delete().eq("batalha_id", batalha_id).execute()
        # Deleta a batalha principal
        res = supabase.table("batalhas").delete().eq("id", batalha_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro [deletar_batalha]: {e}")
        return False


def obter_batalhas_finalizadas():
    """Recupera o histórico de confrontos encerrados do banco."""
    try:
        res = (
            supabase.table("batalhas")
            .select("*, time_a:time_a_id(nome), time_b:time_b_id(nome)")
            .eq("finalizada", True)
            .order("created_at", descending=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"❌ Erro [obter_batalhas_finalizadas]: {e}")
        return []


# ============================================================================
# 4. SUPORTE AUXILIAR: CADASTRO COMPLEMENTAR DE QUESTÕES
# ============================================================================

def cadastrar_questao_rapida(enunciado, alternativas_texto, indice_correta):
    """Cadastra uma questão e insere suas alternativas vinculadas."""
    try:
        res_q = supabase.table("questoes").insert({
            "enunciado": enunciado.strip(),
            "indice_correto": int(indice_correta)
        }).execute()
        
        if not res_q.data:
            return {"sucesso": False, "mensagem": "Erro ao salvar o enunciado da questão."}
            
        questao_id = res_q.data[0]["id"]
        
        lote_alternativas = []
        for i, texto in enumerate(alternativas_texto, start=1):
            lote_alternativas.append({
                "questao_id": questao_id,
                "texto": texto.strip(),
                "ordem": i,
                "correta": (i == (indice_correta + 1))
            })
            
        supabase.table("alternativas").insert(lote_alternativas).execute()
        return {"sucesso": True, "mensagem": "Questão técnica integrada com sucesso!"}
    except Exception as e:
        print(f"❌ Erro [cadastrar_questao_rapida]: {e}")
        return {"sucesso": False, "mensagem": f"Falha operacional: {str(e)}"}