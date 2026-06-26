import streamlit as st
from utils.session import iniciar_session
from extra_streamlit_components import CookieManager

# 1. Inicializa o estado global da sessão do ecossistema
iniciar_session()

# 2. INSTANCIA O GERENCIADOR DE COOKIES DE FORMA DIRETA (SEM CACHE)
# Corrigido o CachedWidgetWarning: O CookieManager precisa rodar livremente a cada rerun
cookie_manager = CookieManager()
minutos_validade = 1440  # Tempo de retenção da sessão (24 horas)

# ============================================================================
# 🚀 ROTEADOR CENTRAL VIA QUERY STRING (QR CODE / LINKS COMPARTILHÁVEIS)
# ============================================================================
query_params = st.query_params

if "sala" in query_params and "id" in query_params:
    tipo_sala = str(query_params["sala"]).strip().lower()
    sala_id = str(query_params["id"]).strip()
    
    # 🔒 Se o utilizador NÃO estiver autenticado, retém o destino para o pós-login
    if st.session_state.get("usuario_logado") is None:
        st.session_state["redirecionamento_pendente"] = {
            "sala": tipo_sala,
            "id": sala_id
        }
    else:
        # 🟢 Se já estiver logado, faz o desvio imediato para a atividade correta
        if tipo_sala == "batalha":
            st.session_state.batalha_ativa_id = sala_id
            st.session_state.pagina = "batalha_rodada"
            
        elif tipo_sala == "quiz":
            st.session_state.quiz_ativo_id = sala_id
            st.session_state.pagina = "quiz_rodada"
            
        elif tipo_sala == "prova":
            st.session_state.prova_ativa_id = sala_id
            st.session_state.pagina = "prova_responder"
            
        # Limpa os parâmetros da URL para permitir navegação livre ao usuário
        st.query_params.clear()

# ============================================================================
# 🗂️ BARRA LATERAL COM SEPARAÇÃO ESTRITA DE PRIVILÉGIOS (PROFESSOR VS ALUNO)
# ============================================================================
usuario_atual = st.session_state.get("usuario_logado")
pagina_atual = st.session_state.pagina

if usuario_atual:
    # Padroniza a string do tipo de usuário para evitar erros de caixa (Maiúscula/Minúscula)
    tipo_usuario = str(usuario_atual.get("tipo_usuario", "aluno")).lower().strip()

    with st.sidebar:
        # Cabeçalho de Identificação do Perfil
        st.markdown(f"### 👤 {usuario_atual.get('nome', 'Usuário')}")
        st.caption(f"Painel do {tipo_usuario.capitalize()}")
        st.divider()
        
        # 🏢 SEÇÃO 1: ESPAÇO COMUM (Visível para Todos)
        st.markdown("### 🏢 Navegação Principal")
        if st.button("🏠 Início / Novidades", use_container_width=True):
            st.session_state.pagina = "dashboard"
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ⚙️ SEÇÃO 2: GOVERNANÇA E GESTÃO (Exclusivo para Professor / Admin)
        if tipo_usuario in ("professor", "admin"):
            st.markdown("### 🛠️ Gestão Acadêmica")
            
            if st.button("⚙️ Gerenciar Batalhas", use_container_width=True):
                st.session_state.pagina = "batalha_gerenciar"
                st.rerun()
                
            if st.button("👥 Gerenciar Equipes", use_container_width=True):
                st.session_state.pagina = "batalha_times"
                st.rerun()
                
            if st.button("👨‍🎓 Alunos & Integrantes", use_container_width=True):
                st.session_state.pagina = "batalha_integrantes"
                st.rerun()
                
            st.markdown("<br>", unsafe_allow_html=True)

        # ⚡ SEÇÃO 3: ARENA DE ATIVIDADES (Visível para Todos)
        st.markdown("### ⚔️ Arena Challenge")
        if st.button("⚔️ Batalha de Equipes", use_container_width=True):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
            
        if st.button("🎮 Quiz ao Vivo", use_container_width=True):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
            
        if st.button("📝 Mini Provas Práticas", use_container_width=True):
            st.session_state.pagina = "mini_provas"
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 🏆 SEÇÃO 4: CRITÉRIOS E SCORE (Visível para Todos)
        st.markdown("### 📈 Desempenho e Regras")
        if st.button("🏅 Central de Pontuações", use_container_width=True):
            st.session_state.pagina = "ranking"
            st.rerun()
            
        if st.button("📖 Regras e Fair Play", use_container_width=True):
            st.session_state.pagina = "regras"
            st.rerun()
            
        # Sistema de Logout Seguro
        st.divider()
        if st.button("🚪 Encerrar Sessão (Sair)", type="primary", use_container_width=True):
            st.session_state.usuario_logado = None
            st.session_state.pagina = "login"
            st.rerun()
# ============================================================================
# 🗺️ ÁRVORE DE NAVEGAÇÃO / RENDERIZAÇÃO DE TELAS (ESTADOS)
# ============================================================================
# Fluxo de Autenticação
if pagina_atual == "login":
    from telas.login import tela_login
    tela_login(cookie_manager=cookie_manager, minutos_validade=minutos_validade)

elif pagina_atual == "cadastro":
    from telas.cadastro import tela_cadastro
    tela_cadastro()

# Dashboard Principal / Home (Corrigido o ModuleNotFoundError apontando para home.py)
elif pagina_atual == "dashboard":
    from telas.home import tela_home
    tela_home()

# Ecossistema: Batalha de Equipes
elif pagina_atual == "batalha_de_equipes":
    from telas.batalha_de_equipes.batalha_de_equipes import tela_batalha_de_equipes
    tela_batalha_de_equipes()

elif pagina_atual == "batalha_gerenciar":
    from telas.batalha_de_equipes.gerenciar_batalhas import tela_batalha_gerenciar
    tela_batalha_gerenciar()

elif pagina_atual == "batalha_rodada":
    from telas.batalha_de_equipes.rodada import tela_batalha_rodada
    tela_batalha_rodada()

# Ecossistema: Quiz Ao Vivo (Síncrono)
elif pagina_atual == "quiz_ao_vivo":
    from telas.quiz_ao_vivo import tela_quiz_ao_vivo
    tela_quiz_ao_vivo()

# Ecossistema: Mini Provas Práticas (Assíncronas)
elif pagina_atual == "mini_provas":
    from telas.mini_provas import tela_mini_provas
    tela_mini_provas()

# Recursos Globais e Tabelas Auxiliares
elif pagina_atual == "ranking":
    from telas.pontuacoes import tela_pontuacoes
    tela_pontuacoes()

elif pagina_atual == "regras":
    from telas.regras import tela_central_regras
    tela_central_regras()

# Fallback de segurança para estados indefinidos
else:
    st.session_state.pagina = "login"
    st.rerun()