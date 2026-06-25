import datetime
from database.conexao import supabase

# ============================================================================
# GERENCIAMENTO DE TIMES & EQUIPES
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
        resposta = supabase.table("times").update({"nome": novo_nome.strip()}).eq("id", time_id).execute()
        return bool(resposta.data and len(resposta.data) > 0)
    except Exception as erro:
        print(f"❌ Erro [editar_time]: {erro}")
        return False

# ============================================================================
# MOTOR DE CONFRONTO E MECÂNICA DE RODADAS (SÍNCRONA)
# ============================================================================

def obter_estado_batalha(batalha_id):
    try:
        res = supabase.table("batalhas").select("*").eq("id", batalha_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"❌ Erro [obter_estado_batalha]: {e}")
        return None

def iniciar_partida_sincrona(batalha_id, time_inicial_id):
    try:
        supabase.table("batalhas").update({
            "status": "em_andamento",
            "pergunta_atual_ordem": 1,
            "time_da_vez_id": time_inicial_id,
            "status_sincrono": "aguardando_resposta"
        }).eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao iniciar partida: {e}")
        return False

def processar_resposta_sincrona(batalha_id, questao_id, time_id, resposta_correta, time_adversario_id, tentativa_numero):
    """
    Mecanismo oficial da Arena Síncrona: Processa com exatidão 6 argumentos posicionalmente.
    """
    try:
        # 1. Regista a submissão do time na tabela de logs
        supabase.table("batalha_respostas").insert({
            "batalha_id": batalha_id,
            "questao_id": questao_id,
            "time_id": time_id,
            "resposta_correta": resposta_correta,
            "tentativa_numero": tentativa_numero
        }).execute()

        # 2. Se o time acertou o alvo
        if resposta_correta is True:
            # Avança o jogo para a próxima pergunta e devolve o turno para o adversário começar
            batalha_atual = obter_estado_batalha(batalha_id)
            nova_ordem = int(batalha_atual.get("pergunta_atual_ordem", 1)) + 1
            
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": nova_ordem,
                "time_da_vez_id": time_adversario_id,
                "status_sincrono": "aguardando_resposta"
            }).eq("id", batalha_id).execute()
            
        else:
            # Se errou na 1ª tentativa, ativa a mecânica de REBATE (o adversário tenta responder a mesma questão)
            if tentativa_numero == 1:
                supabase.table("batalhas").update({
                    "time_da_vez_id": time_adversario_id,
                    "status_sincrono": "rebate_ativo"
                }).eq("id", batalha_id).execute()
            else:
                # Se errou na 2ª tentativa (no rebate), ninguém pontua e passa para a próxima pergunta
                batalha_atual = obter_estado_batalha(batalha_id)
                nova_ordem = int(batalha_atual.get("pergunta_atual_ordem", 1)) + 1
                
                # Turno passa para o time que não falhou o rebate agora
                supabase.table("batalhas").update({
                    "pergunta_atual_ordem": nova_ordem,
                    "time_da_vez_id": time_id, 
                    "status_sincrono": "aguardando_resposta"
                }).eq("id", batalha_id).execute()
                
        return True
    except Exception as e:
        print(f"❌ Erro em [processar_resposta_sincrona]: {e}")
        return False

def encerra_partida_sincrona(batalha_id):
    # Aliás mantido por compatibilidade de escrita
    return encerrar_partida_sincrona(batalha_id)

def encerrar_partida_sincrona(batalha_id):
    try:
        supabase.table("batalhas").update({
            "finalizada": True,
            "status": "finalizada"
        }).eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao encerrar partida: {e}")
        return False

# 🚀 REINTRODUZIDO: Função exigida por outras telas da aplicação para limpar o erro de importação
def deletar_batalha(batalha_id):
    try:
        supabase.table("batalha_perguntas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalha_respostas").delete().eq("batalha_id", batalha_id).execute()
        supabase.table("batalhas").delete().eq("id", batalha_id).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao deletar batalha: {e}")
        return False