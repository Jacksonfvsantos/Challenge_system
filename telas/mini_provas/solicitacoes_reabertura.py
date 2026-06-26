import streamlit as st

def tela_solicitacoes_reabertura():
    st.title("Solicitações de Reabertura")

    for i in range(2):
        with st.container(border=True):
            st.write("Aluno: João")
            st.write("Motivo: minha internet caiu")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Aprovar {i}", use_container_width=True):
                    st.success("Solicitação aprovada")
            with col2:
                if st.button(f"Recusar {i}", use_container_width=True):
                    st.error("Solicitação recusada")

    st.divider()

    if st.button("Voltar", use_container_width=True):
        # Roteia de volta ao painel de gerenciamento do docente
        st.session_state.pagina = "batalha_gerenciar"
        st.rerun()