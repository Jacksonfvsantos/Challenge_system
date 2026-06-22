from database.conexao import supabase

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
