import streamlit as st
import datetime
from services.mini_prova_service import listar_mini_provas
from utils.estilo import aplicar_estilo, cabecalho

def tela_mini_provas():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho("Mini-provas", "Realize as provas disponíveis e modularizadas")

    if tipo == "professor":
        if st.button("➕ Criar Nova Mini Prova ou Fazer Upload", type="primary", use_container_width=True):
            st.session_state.pagina = "mini_provas_professor"
            st.rerun()
        st.divider()

    mini_provas = listar_mini_provas()
    provas_ativas = [p for p in mini_provas if p.get("status") == "Disponível"]

    st.markdown("### 📋 Provas Ativas")
    if not provas_ativas:
        st.info("Nenhuma mini prova em andamento.")
    
    for prova in provas_ativas:
        # Mantendo o layout de card limpo e funcional
        with st.container(border=True):
            st.markdown(f"""
            <strong style="color:#0d1b2a; font-size:16px;">{prova.get('titulo', 'Sem Título')}</strong><br>
            <span style="color:#555; font-size:13px;">{prova.get('descricao', 'Sem descrição.')}</span><br>
            <span style="color:#00b4d8; font-size:12px; font-weight:600;">
                📝 {prova.get('quantidade_questoes', 0)} Questões &nbsp;|&nbsp; ⏱️ {prova.get('duracao_minutos', 0)} min
            </span>
            """, unsafe_allow_html=True)
            
            # Botão de Ação real (Streamlit) posicionado abaixo do conteúdo
            if st.button(f"Iniciar {prova.get('titulo', 'Prova')}", key=f"run_{prova['id']}", type="primary", use_container_width=True):
                st.session_state.prova_ativa_id = prova["id"]
                st.session_state.pagina = "realizar_mini_prova"
                st.rerun()