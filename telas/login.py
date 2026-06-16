import streamlit as st
import datetime
from services.auth_service import login_usuario

def tela_login(cookie_manager, minutos_validade):
    """
    Renderiza a interface de autenticação e injeta o token de sessão 
    no navegador do cliente em caso de credenciais válidas.
    """
    
    # Centraliza o container de login usando colunas de preenchimento
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #1b3a5c; margin-bottom: 5px;">🔒 Challenge System</h2>
            <p style="color: #666; font-size: 14px;">Insira suas credenciais corporativas para acessar a arena</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            email = st.text_input(
                "E-mail:", 
                placeholder="exemplo@gmail.com",
                key="login_email_input"
            )
            
            senha = st.text_input(
                "Senha de acesso:", 
                type="password", 
                placeholder="••••••••",
                key="login_senha_input"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_entrar = st.button(
                "Entrar no Sistema", 
                type="primary", 
                use_container_width=True,
                key="btn_executar_login"
            )
            
            if btn_entrar:
                # 1. Valida o preenchimento dos campos antes de chamar o banco
                if not email.strip() or not senha:
                    st.error("Por favor, preencha todos os campos de login.")
                else:
                    # 2. Consulta o serviço de autenticação
                    usuario = login_usuario(email, senha)
                    
                    if usuario:
                        # 3. Alimenta o Session State para uso imediato do Streamlit
                        st.session_state.usuario_logado = usuario
                        st.session_state.pagina = "home"
                        
                        # 4. Calcula a data de expiração futura (X minutos adiante)
                        data_expiracao = datetime.datetime.now() + datetime.timedelta(minutes=int(minutos_validade))
                        
                        try:
                            # 5. Grava o cookie de sessão persistente no navegador do usuário
                            cookie_manager.set(
                                cookie="user_session_token",
                                value=usuario,
                                expires_at=data_expiracao,
                                key="login_session_setter"
                            )
                            st.success("Autenticação bem-sucedida! Redirecionando...")
                        except Exception as e:
                            # Fallback caso o navegador bloqueie cookies de terceiros
                            print(f"⚠️ Alerta de escrita de Cookie: {e}")
                            st.warning("Login efetuado, mas a retenção de F5 pode estar desativada no seu navegador.")
                        
                        # Força o recarregamento instantâneo já com o novo estado injetado
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos. Por favor, verifique suas credenciais.")
                        
        # Link complementar de navegação para a tela de cadastro
        st.markdown("<br>", unsafe_allow_html=True)
        col_link1, col_link2 = st.columns([2, 1])
        with col_link1:
            st.caption("Ainda não possui uma conta de acesso?")
        with col_link2:
            if st.button("Cadastre-se", key="btn_goto_cadastro", use_container_width=True):
                st.session_state.pagina = "cadastro"
                st.rerun()