from database.conexao import supabase

# ============================================================================
# 1. GESTÃO DE EQUIPES E MEMBROS (O QUE VOCÊ JÁ TINHA)
# ============================================================================

def aluno_criar_e_entrar_no_time(nome_time, usuario_id):
    """Cria o time e vincula o aluno criador como primeiro membro automaticamente."""
    try:
        # 1. Cria o time no banco
        res_time = supabase.table("times").insert({"nome": nome_time.strip()}).execute()
        
        if not res_time.data:
            return {"sucesso": False, "mensagem": "Erro ao registrar o nome do time (pode já existir)."}
            
        time_id = res_time.data[0]["id"]
        
        # 2. Vincula o aluno como membro desse time
        res_membro = supabase.table("time_membros").insert({
            "time_id": time_id,
            "usuario_id": usuario_id
        }).execute()
        
        if res_membro.data:
            return {"sucesso": True, "mensagem": f"Equipe '{nome_time}' criada com sucesso!"}
        return {"sucesso": False, "mensagem": "Time criado, mas falha ao vincular seu perfil."}
    except Exception as e:
        print(f"❌ Erro [aluno_criar_e_entrar_no_time]: {e}")
        return {"sucesso": False, "mensagem": "Erro interno de comunicação com o servidor."}

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
# 2. ORQUESTRAÇÃO E GERENCIAMENTO SÍNCRONO (ADICIONADO PARA O PROFESSOR)
# ============================================================================

def iniciar_partida_sincrona(batalha_id, primeiro_time_id):
    """Muda o status da batalha para em_andamento e define quem começa jogando."""
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

def liberar_proxima_pergunta(batalha_id, nova_ordem, proximo_time_id):
    """Avança a rodada mudando o ponteiro da pergunta que os alunos visualizam."""
    try:
        res = supabase.table("batalhas").update({
            "pergunta_atual_ordem": nova_ordem,
            "status_sincrono": "aguardando_resposta",
            "time_da_vez_id": proximo_time_id
        }).eq("id", batalha_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro [liberar_proxima_pergunta]: {e}")
        return False
