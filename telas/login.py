import streamlit as st
import datetime
from services.auth_service import login_usuario

def tela_login(cookie_manager, minutos_validade):
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #1b3a5c; margin-bottom: 5px;">🔒 Challenge System</h2>
            <p style="color: #94a3b8; font-size: 14px;">Insira suas credenciais corporativas para acessar a arena</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("formulario_autenticacao_sincrona", clear_on_submit=False):
            email = st.text_input("E-mail institucional:", placeholder="exemplo@unijorge.edu.br", key="login_email_input")
            senha = st.text_input("Senha de acesso:", type="password", placeholder="••••••••", key="login_senha_input")
            st.markdown("<br>", unsafe_allow_html=True)
            btn_entrar = st.form_submit_button("Entrar no Sistema", type="primary", use_container_width=True)
            
            if btn_entrar:
                if not email.strip() or not senha:
                    st.error("Por favor, preencha todos os campos de login.")
                else:
                    usuario = login_usuario(email, senha)
                    if usuario:
                        st.session_state.usuario_logado = usuario
                        redirecionamento = st.session_state.get("redirecionamento_pendente")
                        
                        if redirecionamento:
                            tipo_sala = redirecionamento["sala"]
                            sala_id = redirecionamento["id"]
                            if tipo_sala == "batalha":
                                st.session_state.batalha_ativa_id = sala_id
                                st.session_state.pagina = "batalha_rodada"
                            elif tipo_sala == "quiz":
                                st.session_state.quiz_ativo_id = sala_id
                                st.session_state.pagina = "quiz_rodada"
                            elif tipo_sala == "prova":
                                st.session_state.prova_ativa_id = sala_id
                                st.session_state.pagina = "prova_responder"
                            del st.session_state["redirecionamento_pendente"]
                        else:
                            st.session_state.pagina = "home"
                        
                        data_expiracao = datetime.datetime.now() + datetime.timedelta(minutes=int(minutos_validade))
                        try:
                            cookie_manager.set(
                                cookie="user_session_token",
                                value=usuario,
                                expires_at=data_expiracao,
                                key="login_session_setter"
                            )
                            st.success("Autenticação bem-sucedida! Redirecionando...")
                        except Exception as e:
                            print(f"⚠️ Erro ao registrar cookie no navegador: {e}")
                            st.warning("Login efetuado, mas a retenção de sessão pode falhar neste navegador.")
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos. Por favor, verifique suas credenciais.")
                        
        st.markdown("<br>", unsafe_allow_html=True)
        col_link1, col_link2 = st.columns([2, 1])
        with col_link1:
            st.caption("Ainda não possui uma conta de acesso?")
        with col_link2:
            if st.button("Cadastre-se", key="btn_goto_cadastro", use_container_width=True):
                st.session_state.pagina = "cadastro"
                st.rerun()