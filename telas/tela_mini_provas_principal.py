import streamlit as st
import datetime
from services.mini_prova_service import listar_mini_provas
from utils.estilo import aplicar_estilo, cabecalho, formatar_titulo_aba

def tela_mini_provas():
    aplicar_estilo()
    cabecalho("Avaliações Modulares", "Realize as provas disponíveis e acompanhe seu desempenho")


    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    if tipo_usuario in ("professor", "admin"):
        if st.button("➕ Nova Mini-Prova", type="primary"): 
            st.session_state.pagina = "mini_provas_professor"
            st.rerun()
        st.divider()

    formatar_titulo_aba("Provas Ativas")
    mini_provas = listar_mini_provas()
    provas_ativas = [p for p in mini_provas if p.get("status") == "Disponível"]

    st.markdown("### 📋 Provas Ativas")
    if not provas_ativas:
        st.info("Nenhuma mini prova em andamento.")
    
    for prova in provas_ativas:
        prova_id = prova.get("id")
        with st.container(border=True):
            st.markdown(f"""
            <strong style="color:#0d1b2a; font-size:16px;">{prova.get('titulo', 'Sem Título')}</strong><br>
            <span style="color:#555; font-size:13px;">{prova.get('descricao', 'Sem descrição.')}</span><br>
            <span style="color:#00b4d8; font-size:12px; font-weight:600;">
                📝 {prova.get('quantidade_questoes', 0)} Questões &nbsp;|&nbsp; ⏱️ {prova.get('duracao_minutos', 0)} min
            </span>
            """, unsafe_allow_html=True)
            
            st.write("")
            if tipo_usuario == "aluno":
                if st.button("🚀 Iniciar Prova", key=f"start_{prova_id}", type="primary", use_container_width=True):
                    st.session_state.prova_ativa_id = prova_id
                    st.session_state.pagina = "realizar_mini_prova"
                    st.rerun()
            
            # --- INTEGRAÇÃO DO QR CODE (REQUISITO DE RELATÓRIO) ---
            if tipo_usuario in ("professor", "admin"):
                with st.expander("📡 Painel de Compartilhamento (QR Code / Link)"):
                    from utils.compartilhamento import exibir_painel_compartilhamento
                    exibir_painel_compartilhamento("mini_prova", prova_id)