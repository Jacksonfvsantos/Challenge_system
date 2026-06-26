import streamlit as st
from utils.session import iniciar_session
from extra_streamlit_components import CookieManager

# 1. Inicializa o estado global da sessão do ecossistema
iniciar_session()

cookie_manager = CookieManager()
minutos_validade = 1440  # Exemplo: 24 horas (ajuste para o valor desejado)

# ============================================================================
# 🚀 ROTEADOR CENTRAL VIA QUERY STRING (QR CODE / LINKS COMPARTILHÁVEIS)
# ============================================================================
query_params = st.query_params

if "sala" in query_params and "id" in query_params:
    tipo_sala = str(query_params["sala"]).strip().lower()
    sala_id = str(query_params["id"]).strip()
    
    # 🔒 Se o utilizador NÃO estiver autenticado, retém o destino para pós-login
    if st.session_state.get("usuario_logado") is None:
        st.session_state["redirecionamento_pendente"] = {
            "sala": tipo_sala,
            "id": sala_id
        }
    else:
        # 🟢 Se já estiver logado, faz o desvio imediato para a sala correspondente
        if tipo_sala == "batalha":
            st.session_state.batalha_ativa_id = sala_id
            st.session_state.pagina = "batalha_rodada"
            
        elif tipo_sala == "quiz":
            st.session_state.quiz_ativo_id = sala_id
            st.session_state.pagina = "quiz_rodada"  # Alinhe com o nome exato da sua tela ativa de Quiz
            
        elif tipo_sala == "prova":
            st.session_state.prova_ativa_id = sala_id
            st.session_state.pagina = "prova_responder"  # Alinhe com o nome exato da sua tela ativa de Provas
            
        # Limpa os parâmetros da URL da barra do navegador para permitir navegação livre posterior
        st.query_params.clear()

# ============================================================================
# 🗺️ ÁRVORE DE NAVEGAÇÃO / RENDERIZAÇÃO DE TELAS (ESTADOS)
# ============================================================================
pagina_atual = st.session_state.pagina

# Fluxo de Autenticação
if pagina_atual == "login":
    from telas.login import tela_login
    
    # ✅ CORRIGIDO: Injetando os argumentos exigidos pela assinatura da função
    # (Substitua pelos nomes exatos das suas instâncias de cookies declaradas no topo do app.py se mudarem)
    tela_login(cookie_manager=cookie_manager, minutos_validade=minutos_validade)

elif pagina_atual == "cadastro":
    from telas.cadastro import tela_cadastro
    tela_cadastro()

# Dashboard Principal / Home
elif pagina_atual == "dashboard":
    from telas.dashboard import tela_dashboard
    tela_dashboard()

# ⚔️ Ecossistema: Batalha de Equipes
elif pagina_atual == "batalha_de_equipes":
    from telas.batalha_de_equipes.batalha_de_equipes import tela_batalha_de_equipes
    tela_batalha_de_equipes()

elif pagina_atual == "batalha_gerenciar":
    from telas.batalha_de_equipes.gerenciar_batalhas import tela_batalha_gerenciar
    tela_batalha_gerenciar()

elif pagina_atual == "batalha_rodada":
    from telas.batalha_de_equipes.rodada import tela_batalha_rodada
    tela_batalha_rodada()

elif pagina_atual == "batalha_times":
    from telas.batalha_de_equipes.times import tela_batalha_times
    tela_batalha_times()

elif pagina_atual == "batalha_integrantes":
    from telas.batalha_de_equipes.integrantes import tela_batalha_integrantes
    tela_batalha_integrantes()

elif pagina_atual == "batalha_regras":
    from telas.batalha_de_equipes.regras import tela_batalha_regras
    tela_batalha_regras()

# 🧠 Ecossistema: Quiz Ao Vivo (Síncrono)
elif pagina_atual == "quiz_ao_vivo":
    from telas.quiz_ao_vivo.quiz_main import tela_quiz_main  # Ajuste para os seus caminhos reais
    tela_quiz_main()

elif pagina_atual == "quiz_rodada":
    from telas.quiz_ao_vivo.quiz_rodada import tela_quiz_rodada
    tela_quiz_rodada()

# 📝 Ecossistema: Mini Provas Práticas (Assíncronas)
elif pagina_atual == "mini_provas":
    from telas.mini_provas.provas_main import tela_provas_main
    tela_provas_main()

elif pagina_atual == "prova_responder":
    from telas.mini_provas.prova_responder import tela_prova_responder
    tela_prova_responder()

# 🏆 Recursos Globais (Ranking, Recompensas e Perfil)
elif pagina_atual == "ranking":
    from telas.ranking import tela_ranking
    tela_ranking()

elif pagina_atual == "recompensas":
    from telas.recompensas import tela_recompensas
    tela_recompensas()

# Tratamento de Fallback de segurança para estados corrompidos
else:
    st.session_state.pagina = "login"
    st.rerun()