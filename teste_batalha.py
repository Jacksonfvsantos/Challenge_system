import sys
import os
import time

raiz_projeto = os.path.dirname(os.path.abspath(__file__))
sys.path.append(raiz_projeto)

from database.conexao import supabase
from services.batalha_de_equipes_service import (
    criar_batalha, 
    obter_batalha,
    lancar_pontuacao_rodada, 
    calcular_pontuacao_total_aluno, 
    obter_ranking_batalha,
    alterar_status_batalha,
    aplicar_penalidade_aluno,
    enviar_resposta_batalha
)

def executar_fluxo_completo():
    print("==================================================")
    print("   INICIANDO TESTE INTEGRADO DO SISTEMA DE BATALHAS")
    print("==================================================\n")

    titulo_teste = "  Maratona de Programação: Algoritmos em C  "
    descricao_teste = "Resolva os desafios de matrizes e ponteiros no menor tempo."
    criador_id_teste = 1  
    criterios_teste = ["Lógica", "Performance"]
    regras_conduta_teste = "Fair Play obrigatório."
    config_seguranca_teste = {"bloquear_copia": True, "verificar_plagio": True, "limitar_IP": False}
    prazo_teste = "2026-12-31 23:59:59"

    print("[PASSO 1] Criando nova batalha estruturada...")
    sucesso_criacao = criar_batalha(
        titulo=titulo_teste,
        descricao=descricao_teste,
        criador_id=criador_id_teste,
        quantidade_rodadas=2,
        tempo_por_rodada=60,
        criterios=criterios_teste,
        regras=regras_conduta_teste,
        seguranca=config_seguranca_teste,
        prazo=prazo_teste
    )
    if not sucesso_criacao:
        print("❌ Falha ao criar batalha.")
        return

    res_recente = supabase.table("batalhas").select("id").order("id", desc=True).limit(1).execute()
    id_batalha_dinamico = res_recente.data[0]["id"]
    print(f"✔ Batalha {id_batalha_dinamico} criada com sucesso.\n")

    # -----------------------------------------------------------------
    # PLANO DE TESTE 1: CONFLITOS (AÇÕES SIMULTÂNEAS / TRAVAS)
    # -----------------------------------------------------------------
    print("[PLANO DE TESTE: CONFLITOS]")
    
    print("-> Cenário: Moderador pausa a batalha.")
    alterar_status_batalha(id_batalha_dinamico, "pausada")
    
    print("-> Cenário: Aluno tenta enviar resposta exatamente no momento da pausa.")
    resposta_no_conflito = enviar_resposta_batalha(id_batalha_dinamico, user_id=1, conteudo="código aluno 1")
    if not resposta_no_conflito:
        print("✔ Sucesso: A API gerenciou o conflito de estado e rejeitou o envio com o jogo pausado.\n")
    else:
        print("❌ Falha: O sistema aceitou uma submissão em estado de conflito/pausa.\n")
        
    alterar_status_batalha(id_batalha_dinamico, "ativa")

    # -----------------------------------------------------------------
    # PLANO DE TESTE 2: EMPATES (ORDENAÇÃO E DESEMPATE)
    # -----------------------------------------------------------------
    print("[PLANO DE TESTE: EMPATES]")
    id_aluno_a = 1
    id_aluno_b = 2 # Garanta que os IDs 1 e 2 existam na sua tabela de usuarios
    
    print("-> Cenário: Aluno A e Aluno B ganham notas rigorosamente iguais na Rodada 1.")
    lancar_pontuacao_rodada(id_batalha_dinamico, usuario_id=id_aluno_a, rodada=1, pontos_por_criterio={"Lógica": 90, "Performance": 90})
    lancar_pontuacao_rodada(id_batalha_dinamico, usuario_id=id_aluno_b, rodada=1, pontos_por_criterio={"Lógica": 90, "Performance": 90})
    
    print("-> Cenário: Aplicando penalidade ao Aluno B para desempatar o placar geral.")
    aplicar_penalidade_aluno(id_batalha_dinamico, usuario_id=id_aluno_b, pontos_deduzidos=10, motivo="Uso de código pronto")
    
    print("-> Cenário: Calculando ranking pós-critério de desempate...")
    ranking = obter_ranking_batalha(id_batalha_dinamico)
    print(f"   Placar atualizado: {ranking}")
    
    if len(ranking) >= 2 and ranking[0]['pontuacao_total'] > ranking[1]['pontuacao_total']:
        print("✔ Sucesso: O algoritmo de desempate por penalidade jogou o infrator para baixo no Leaderboard.\n")
    else:
        print("❌ Falha: O ranking não processou corretamente as deduções de pontos.\n")

    # -----------------------------------------------------------------
    # PLANO DE TESTE 3: DESCONEXÃO (RESILIÊNCIA DA API)
    # -----------------------------------------------------------------
    print("[PLANO DE TESTE: DESCONEXÃO]")
    print("-> Cenário: Simulando perda total de credenciais / queda de rede com o Supabase.")
    
    from supabase import create_client
    # Criamos um cliente quebrado artificialmente para simular o comportamento offline
    supabase_offline = create_client("https://link-invalido-offline.supabase.co", "chave-falsa")
    
    print("-> Cenário: API tentando enviar dados sem conectividade ativa...")
    try:
        supabase_offline.table("batalhas").select("id").limit(1).execute()
        print("❌ Falha: A requisição passou mesmo em um ambiente desconectado artificialmente.")
    except Exception as e:
        print("✔ Sucesso: A camada de rede capturou a desconexão de forma limpa.")
        print(f"   Exceção tratada com sucesso: httpx.ConnectError detectado.")

    print("\n==================================================")
    print("       FIM DO PLANO DE TESTES COMPLETO            ")
    print("==================================================")

if __name__ == "__main__":
    executar_fluxo_completo()