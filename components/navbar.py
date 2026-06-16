import streamlit as st

def mostrar_menu(cookie_manager):
    """
    Renderiza a barra lateral com a identificação do usuário no topo,
    menu de navegação vertical e o botão de logout na base.
    """
    # 1. EXIBIÇÃO DO PERFIL DO USUÁRIO NO TOPO DA BARRA LATERAL
    usuario = st.session_state.get("usuario_logado", {})
    nome_usuario = usuario.get("nome", "Usuário")
    perfil_usuario = str(usuario.get("tipo_usuario", "aluno")).upper()
    
    with st.sidebar.container(border=True):
        st.markdown(f"""
        <div style="font-size: 13px; line-height: 1.5; text-align: center;">
            <p style="margin: 0; color: #777; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">Sessão Ativa</p>
            <h4 style="margin: 5px 0; color: #1b3a5c;">👤 {nome_usuario}</h4>
            <span style="background:#edf2f7; color:#2d3748; padding:2px 8px; border-radius:10px; font-size: 10px; font-weight: bold;">
                {perfil_usuario}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
    st.sidebar.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 10px;">
        <h5 style="color: #1b3a5c; margin-bottom: 0;">🗺️ Menu Principal</h5>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. BOTÕES DE NAVEGAÇÃO DO CORE CORPORATIVO
    if st.sidebar.button("🏠 Início / Dashboard", use_container_width=True):
        st.session_state.pagina = "home"
        st.rerun()
        
    if st.sidebar.button("🎯 Desafios Operacionais", use_container_width=True):
        st.session_state.pagina = "desafios"
        st.rerun()
        
    if st.sidebar.button("🗳️ Avaliação e Votos", use_container_width=True):
        st.session_state.pagina = "votacao"
        st.rerun()

    # 3. BOTÕES DE RECURSOS SÍNCRONOS E GAMIFICAÇÃO
    st.sidebar.divider()
    
    if st.sidebar.button("🎮 Quiz ao Vivo (Sala)", use_container_width=True):
        st.session_state.pagina = "quiz_ao_vivo"
        st.rerun()
        
    if st.sidebar.button("⚔️ Batalha de Equipes", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()
        
    if st.sidebar.button("📝 Mini Provas Práticas", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()

    if st.sidebar.button("🏆 Vitrine de Recompensas", use_container_width=True):
        st.session_state.pagina = "recompensas"
        st.rerun()

    # 4. CRITÉRIOS DE AUDITORIA E LEADERBOARD
    st.sidebar.divider()
    
    if st.sidebar.button("📊 Placar Global de Líderes", use_container_width=True):
        st.session_state.pagina = "pontuacoes"
        st.rerun()
        
    if st.sidebar.button("📖 Manual e Fair Play", use_container_width=True):
        st.session_state.pagina = "regras_plataforma"
        st.rerun()

    # 5. SAÍDA SEGURA DA SESSÃO (MANTIDA NO FINAL)
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Sair do Sistema", type="primary", use_container_width=True, key="btn_sidebar_logout"):
        try:
            cookie_manager.delete("user_session_token")
        except Exception:
            pass
            
        st.session_state.usuario_logado = None
        st.session_state.pagina = "login"
        st.rerun()