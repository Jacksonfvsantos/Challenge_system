import streamlit as st

def mostrar_menu(cookie_manager):
    usuario = st.session_state.get("usuario_logado", {})
    nome_usuario = usuario.get("nome", "Usuário")
    perfil_usuario = str(usuario.get("tipo_usuario", "aluno")).upper()
    
    cor_badge_fundo = "#1e3a8a" if perfil_usuario == "PROFESSOR" else "#065f46"
    cor_badge_texto = "#93c5fd" if perfil_usuario == "PROFESSOR" else "#a7f3d0"
    badge_emoji = "👨‍🏫" if perfil_usuario == "PROFESSOR" else "👨‍🎓"

    with st.sidebar.container(border=True):
        st.markdown(f"""
        <div style="text-align: center; padding: 5px 0;">
            <p style="margin: 0; color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;">
                Sessão Ativa
            </p>
            <h3 style="margin: 8px 0 4px 0; color: #ffffff; font-size: 18px; font-weight: 700; letter-spacing: -0.5px;">
                {nome_usuario}
            </h3>
            <div style="display: inline-block; background-color: {cor_badge_fundo}; color: {cor_badge_texto}; 
                        padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700; 
                        margin-top: 4px; border: 1px solid {cor_badge_texto}33;">
                {badge_emoji} {perfil_usuario}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.sidebar.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 10px;">
        <h5 style="color: #1b3a5c; margin-bottom: 0;">🗺️ Menu Principal</h5>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🏠 Início / Dashboard", use_container_width=True):
        st.session_state.pagina = "home"
        st.rerun()
        
    if st.sidebar.button("🎯 Desafios Operacionais", use_container_width=True):
        st.session_state.pagina = "desafios"
        st.rerun()
        
    if st.sidebar.button("🗳️ Avaliação e Votos", use_container_width=True):
        st.session_state.pagina = "votacao"
        st.rerun()

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

    st.sidebar.divider()
    
    if st.sidebar.button("📊 Placar Global de Líderes", use_container_width=True):
        st.session_state.pagina = "pontuacoes"
        st.rerun()
        
    if st.sidebar.button("📖 Manual e Fair Play", use_container_width=True):
        st.session_state.pagina = "regras_plataforma"
        st.rerun()

    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Sair do Sistema", type="primary", use_container_width=True, key="btn_sidebar_logout"):
        try:
            cookie_manager.delete("user_session_token")
        except Exception:
            pass
            
        st.session_state.usuario_logado = None
        st.session_state.pagina = "login"
        st.rerun()