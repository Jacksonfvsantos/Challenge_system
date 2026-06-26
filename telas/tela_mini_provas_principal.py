import streamlit as st
from services.mini_prova_service import listar_mini_provas
from utils.compartilhamento import exibir_painel_compartilhamento
from utils.estilo import aplicar_estilo, cabecalho

def tela_mini_provas():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    if "alto_contraste" not in st.session_state:
        st.session_state.alto_contraste = False

    if st.session_state.alto_contraste:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: black;
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    cabecalho("Mini-provas", "Realize as provas disponíveis")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Minha Pontuação", use_container_width=True):
            st.session_state.pagina = "pontuacao_mini_provas"
            st.rerun()

    with col2:
        if st.button("Desempenho", use_container_width=True):
            st.session_state.pagina = "desempenho_mini_provas"
            st.rerun()

    with col3:
        with st.popover("Acessibilidade", use_container_width=True):
            alto = st.checkbox("Alto contraste", value=st.session_state.alto_contraste)
            st.session_state.alto_contraste = alto
            st.checkbox("Leitura por questão")
            st.divider()
            st.subheader("Solicitar tempo extra")
            
            if st.button("Enviar solicitação", use_container_width=True):
                st.success("Solicitação enviada")

    st.divider()

    pesquisa = st.text_input("Pesquisar mini prova")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Mini Provas Disponíveis")
    with col2:
        if st.button("Resultados", use_container_width=True):
            st.session_state.pagina = "resultados_mini_provas"
            st.rerun()

    mini_provas = listar_mini_provas()

    if pesquisa:
        mini_provas = [p for p in mini_provas if pesquisa.lower() in str(p.get("titulo", "")).lower()]

    if not mini_provas:
        st.info("Nenhuma mini prova disponível no momento.")
        return

    for prova in mini_provas:
        with st.container(border=True):
            st.markdown(f"""
            <div style="background:#f0f9ff; border-left:4px solid #00b4d8; border-radius:8px; padding:14px 18px; margin-bottom:10px;">
                <strong style="color:#0d1b2a; font-size:15px;">{prova.get('titulo', 'Sem Título')}</strong><br>
                <span style="color:#555; font-size:13px;">{prova.get('descricao', 'Sem descrição definida.')}</span><br>
                <span style="color:#00b4d8; font-size:12px;">📚 Disciplina: {prova.get('disciplina', '-')} | 📝 Questões: {prova.get('qtde_questoes', '-')}</span>
            </div>
            """, unsafe_allow_html=True)

            if tipo_usuario == "aluno":
                if st.button(f"🎯 Fazer Prova", key=f"run_p_{prova['id']}", type="primary", use_container_width=True):
                    st.session_state.prova_ativa_id = prova["id"]
                    st.session_state.pagina = "realizar_mini_prova"
                    st.rerun()
            else:
                with st.expander("📢 Mapeamento de Links & QR Code para Alunos", expanded=False):
                    exibir_painel_compartilhamento(tipo_sala="prova", sala_id=prova["id"])