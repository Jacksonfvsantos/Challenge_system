import streamlit as st

<<<<<<< HEAD
def mostrar_menu():
    """Gera a barra de navegação lateral padronizada para todo o ecossistema."""
    
    usuario = st.session_state.get("usuario_logado", {})
    nome = usuario.get("nome", "Usuário")
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()

    # --- TOPO DA NAVBAR (Identificação Visual do Perfil Logado) ---
    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0d1b2a, #1b3a5c);
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #00b4d8;
    ">
        <p style="margin: 0; color: #90caf9; font-size: 12px; font-weight: 600; text-transform: uppercase;">Acesso Autorizado</p>
        <h4 style="margin: 4px 0 0; color: #ffffff; font-size: 16px;">{nome}</h4>
        <span style="color: #00b4d8; font-size: 12px; font-weight: bold;">🎯 {tipo.capitalize()}</span>
    </div>
    """, unsafe_allow_html=True)

    # --- SEÇÃO GERAL: NAVEGAÇÃO PRINCIPAL (Itens Globais, Tópico 6 e 7) ---
    st.sidebar.markdown("### 🖥️ Navegação Principal")
    
    if st.sidebar.button("🏠 Início / Home", use_container_width=True):
        st.session_state.pagina = "home"
        st.clear_cache()
        st.rerun()

    # IMPLEMENTAÇÃO DO TÓPICO 7: Central de Documentação e Regras
    if st.sidebar.button("📖 Manual / Regras", use_container_width=True):
        st.session_state.pagina = "regras_plataforma"
        st.rerun()

    # IMPLEMENTAÇÃO DO TÓPICO 6: Painel de Indicadores e Pontuações
    if st.sidebar.button("🏆 Minhas Pontuações", use_container_width=True):
        st.session_state.pagina = "pontuacoes"
        st.rerun()

    st.sidebar.divider()

    # --- SEÇÃO COMPLEMENTAR: MÓDULOS DE CONTEÚDO ACADÊMICO ---
    st.sidebar.markdown("### 📚 Atividades Acadêmicas")

    if st.sidebar.button("🎯 Central de Desafios", use_container_width=True):
        st.session_state.pagina = "desafios"
        st.rerun()

    if st.sidebar.button("🗳️ Sistema de Votação/Notas", use_container_width=True):
        st.session_state.pagina = "votacao"
        st.rerun()

    if st.sidebar.button("📝 Mini-Provas", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()

    if st.sidebar.button("🎮 Quiz ao Vivo", use_container_width=True):
        st.session_state.pagina = "quiz_ao_vivo"
        st.rerun()

    if st.sidebar.button("⚔️ Batalha de Equipes", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    # --- RECURSOS EXCLUSIVOS: PAINEL DE GESTÃO (Professor / Admin) ---
    if tipo in ("professor", "admin"):
        st.sidebar.divider()
        st.sidebar.markdown("### ⚙️ Painel de Gestão")
        
        # Expanders estratégicos para manter o contexto de navegação ativo (Item 3.54)
        with st.sidebar.expander("🛠️ Atalhos de Mini-Provas", expanded=False):
            if st.button("➕ Cadastrar Questão", key="nv_cad_q", use_container_width=True):
                st.session_state.pagina = "cadastro_perguntas"
                st.rerun()
            if st.button("📋 Ver Questões", key="nv_lst_q", use_container_width=True):
                st.session_state.pagina = "lista_perguntas"
                st.rerun()
            if st.button("🛠️ Nova Mini-Prova", key="nv_cad_p", use_container_width=True):
                st.session_state.pagina = "cadastro_mini_provas"
                st.rerun()
                
        with st.sidebar.expander("👥 Atalhos de Equipes", expanded=False):
            if st.button("🏁 Gerenciar Times", key="nv_bat_t", use_container_width=True):
                st.session_state.pagina = "batalha_times"
                st.rerun()
            if st.button("👥 Alocar Membros", key="nv_bat_i", use_container_width=True):
                st.session_state.pagina = "batalha_integrantes"
                st.rerun()
            if st.button("⚔️ Lançar Rodadas", key="nv_bat_g", use_container_width=True):
                st.session_state.pagina = "batalha_gerenciar"
                st.rerun()

    # --- SEÇÃO DE FINALIZAÇÃO DE SESSÃO ---
    st.sidebar.divider()
    if st.sidebar.button("🚪 Sair do Sistema", type="primary", use_container_width=True):
        st.session_state.usuario_logado = None
        st.session_state.pagina = "login"
        st.rerun()
=======

def mostrar_menu():
    pagina_atual = st.session_state.get("pagina", "home")
    usuario      = st.session_state.usuario_logado

    # CSS injetado ANTES do with st.sidebar para garantir precedência
    st.markdown("""
        <style>
        /* Botoes da sidebar: base transparente */
        [data-testid="stSidebar"] .stButton > button {
            width: 100% !important;
            text-align: left !important;
            background-color: transparent !important;
            border: none !important;
            color: #ffffff !important;
            padding: 0.5rem 1rem !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: background 0.2s !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #00b4d8 !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stButton > button:focus,
        [data-testid="stSidebar"] .stButton > button:active {
            background-color: transparent !important;
            box-shadow: none !important;
        }
        /* Botao ativo: ciano com borda esquerda branca usando o container nativo */
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.botao-ativo) button {
            background-color: #00b4d8 !important;
            color: #ffffff !important;
            border-left: 4px solid #ffffff !important;
            padding-left: 0.85rem !important;
            font-size: 1.02rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    menu_items = [
        ("Home",               "home",               "menu_home"),
        ("Desafios",           "desafios",            "menu_desafios"),
        ("Votação",            "votacao",             "menu_votacao"),
        ("Mini-provas",        "mini_provas",         "menu_miniprovas"),
        ("Quiz ao Vivo",       "quiz_ao_vivo",        "menu_quiz_ao_vivo"),
        ("Batalha de Equipes", "batalha_de_equipes",  "menu_batalha_de_equipes"),
    ]

    # Evita quebrar se o dicionário de usuário não estiver completamente povoado
    if usuario and usuario.get("tipo_usuario") == "admin":
        menu_items.append(("Admin", "admin", "menu_admin"))

    with st.sidebar:
        st.title("Challenge System")
        if usuario:
            st.write(f"Usuário: {usuario.get('nome', 'Usuário')}")
        st.divider()

        for label, pagina, key in menu_items:
            ativo = (pagina_atual == pagina)
            
            # Usamos o st.container para encapsular o botão de forma limpa
            with st.container():
                if ativo:
                    # Injeta uma tag invisível apenas para o CSS identificar este container específico
                    st.markdown('<span class="botao-ativo"></span>', unsafe_allow_html=True)
                
                if st.button(label, key=key, width="stretch"):
                    st.session_state.pagina = pagina
                    st.rerun()

        st.divider()
        if st.button("Sair", key="menu_sair", width="stretch"):
            st.session_state.usuario_logado = None
            st.session_state.pagina = "login"
            st.rerun()
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
