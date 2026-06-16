import streamlit as st

def mostrar_menu(cookie_manager):
    """
    Renderiza o menu de navegação vertical na barra lateral 
    e gerencia as transições de estado de páginas da aplicação.
    """
    st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 15px;">
        <h3 style="color: #1b3a5c; margin-bottom: 0;">🗺️ Navegação</h3>
        <p style="color: #777; font-size: 11px; margin: 0;">Challenge System Ecossistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. BOTÕES DE NAVEGAÇÃO DO CORE CORPORATIVO
    if st.sidebar.button("🏠 Início / Dashboard", use_container_width=True):
        st.session_state.pagina = "home"
        st.rerun()
        
    if st.sidebar.button("🎯 Desafios Operacionais", use_container_width=True):
        st.session_state.pagina = "desafios"
        st.rerun()
        
    if st.sidebar.button("🗳️ Avaliação e Votos", use_container_width=True):
        st.session_state.pagina = "votacao"
        st.rerun()

    # 2. BOTÕES DE RECURSOS SÍNCRONOS E GAMIFICAÇÃO
    st.sidebar.divider()
    
    if st.sidebar.button("🎮 Quiz ao Vivo (Sala)", use_container_width=True):
        st.session_state.pagina = "quiz_ao_vivo"
        st.rerun()
        
    if st.sidebar.button("⚔️ Batalha de Equipes (PPL)", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()
        
    if st.sidebar.button("📝 Mini Provas Práticas", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()

    if st.sidebar.button("🏆 Vitrine de Recompensas", use_container_width=True):
        st.session_state.pagina = "recompensas"
        st.rerun()

    # 3. CRITÉRIOS DE AUDITORIA E LEADERBOARD
    st.sidebar.divider()
    
    if st.sidebar.button("📊 Placar Global de Líderes", use_container_width=True):
        st.session_state.pagina = "pontuacoes"
        st.rerun()
        
    if st.sidebar.button("📖 Manual e Fair Play", use_container_width=True):
        st.session_state.pagina = "regras_plataforma"
        st.rerun()

    # 4. PAINEL DE USUÁRIO E SAÍDA SEGURA
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    
    usuario = st.session_state.get("usuario_logado", {})
    nome_usuario = usuario.get("nome", "Usuário")
    perfil_usuario = str(usuario.get("tipo_usuario", "aluno")).upper()
    
    with st.sidebar.container(border=True):
        st.markdown(f"""
        <div style="font-size: 12px; line-height: 1.4;">
            👤 Conectado: <strong>{nome_usuario}</strong><br>
            💼 Perfil: <code style="font-size: 10px; background:#edf2f7; padding:1px 4px;">{perfil_usuario}</code>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        
        if st.button("🚪 Sair do Sistema", type="primary", use_container_width=True, key="btn_sidebar_logout"):
            # Deleta o cookie do navegador para evitar o login silencioso no F5 após deslogar
            try:
                cookie_manager.delete("user_session_token")
            except Exception:
                pass
                
            # Limpa o estado interno da aplicação Streamlit
            st.session_state.usuario_logado = None
            st.session_state.pagina = "login"
            st.rerun()