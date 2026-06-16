import streamlit as st


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
        st.cache_data.clear()
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