import streamlit as st

def tela_resultados_mini_provas():
    st.title("Resultados")
    st.subheader("Mini provas finalizadas")

    # Exemplo simulado de iteração sobre o histórico (substituível pela chamada do banco)
    for i in range(3):
        with st.container(border=True):
            st.write(f"Mini Prova {i+1}")
            st.write("Nota: 8.0")
            st.write("Pontuação: 0.8")

            if st.button(f"Ver resultado detalhado", key=f"ver_res_{i}", use_container_width=True):
                # Guarda o contexto de qual prova visualizar e muda de página
                st.session_state.pagina = "resultado_mini_prova"
                st.rerun()

    st.divider()

    if st.button("Voltar", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()