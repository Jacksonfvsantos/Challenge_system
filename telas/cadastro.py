import streamlit as st
import time
from services.auth_service import cadastrar_usuario
from utils.estilo import aplicar_estilo

def tela_cadastro():
    aplicar_estilo()
    
    with st.container():
        st.markdown("""
        <div style="background-color: #1b3a5c; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">Criar conta</h2>
            <p style="color: #93c5fd; margin: 0;">Preencha os dados para se cadastrar</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_cadastro", clear_on_submit=False):
            nome = st.text_input("Nome completo", placeholder="Seu nome")
            email = st.text_input("E-mail", placeholder="seu@email.com")
            
            # 🚨 O campo de 'Tipo de usuário' foi removido daqui
            
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            confirmar_senha = st.text_input("Confirmar senha", type="password", placeholder="••••••••")
            
            btn_cadastrar = st.form_submit_button("Cadastrar", use_container_width=True)
            
            if btn_cadastrar:
                if not nome.strip() or not email.strip() or not senha.strip():
                    st.error("Preencha todos os campos.")
                elif senha != confirmar_senha:
                    st.error("As senhas não conferem.")
                else:
                    # 🚨 Chamada atualizada apenas com os 3 parâmetros
                    resultado = cadastrar_usuario(nome, email, senha)
                    
                    if resultado == "ok":
                        st.success("✅ Conta criada com sucesso! Você foi registrado como Aluno.")
                        time.sleep(1.5)
                        st.session_state.pagina = "login"
                        st.rerun()
                    else:
                        st.error(resultado)
        
        st.write("")
        if st.button("Voltar para o login", use_container_width=True):
            st.session_state.pagina = "login"
            st.rerun()