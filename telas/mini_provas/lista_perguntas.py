import streamlit as st
<<<<<<< HEAD
from services.mini_prova_service import listar_perguntas, excluir_pergunta
from utils.estilo import aplicar_estilo, cabecalho

def tela_lista_perguntas():
    aplicar_estilo()
    
    cabecalho(
        "Questões Cadastradas",
        "Visualize, audite ou remova as perguntas armazenadas no banco unificado"
    )

    # Chamada segura mapeada com try-catch interno na camada de serviço (Previne Item 3.62)
    perguntas = listar_perguntas()

    if not perguntas:
        st.info("💡 Nenhuma questão localizada no banco de dados para os critérios atuais.")
    else:
        st.caption(f"Total de {len(perguntas)} questões localizadas no repositório.")
        st.markdown("<br>", unsafe_allow_html=True)

        for idx, pergunta in enumerate(perguntas):
            # Limpa e sanitiza o ID alfanumérico UUID para evitar colisões de chaves no Streamlit
            id_limpo = str(pergunta["id"]).strip()
            
            with st.container(border=True):
                st.markdown(f"**Questão {idx + 1}**")
                st.write(pergunta["enunciado"])
                
                nivel_tag = str(pergunta.get('nivel', 'Não informado')).capitalize()
                st.caption(f"📊 **Complexidade:** `{nivel_tag}`")

                col1, col2 = st.columns(2)
                with col1:
                    # Chave gerada de forma combinada e segura contra quebras alfanuméricas
                    if st.button("📝 Editar Questão", key=f"btn_edit_{id_limpo}_{idx}", use_container_width=True):
                        st.session_state.id_pergunta = id_limpo
                        st.session_state.pagina = "editar_pergunta"
                        st.rerun()

                with col2:
                    if st.button("🗑️ Remover do Banco", key=f"btn_del_{id_limpo}_{idx}", use_container_width=True):
                        sucesso = excluir_pergunta(id_limpo)
                        if sucesso:
                            st.success("Questão deletada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Não foi possível excluir. Verifique as restrições de dependência.")

    st.divider()
    if st.button("⬅️ Voltar para o Painel Geral", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()
=======

from services.mini_prova_service import (
    listar_perguntas
)


def tela_lista_perguntas():

    st.title(
        "Perguntas cadastradas"
    )

    perguntas = listar_perguntas()

    if not perguntas:

        st.info(
            "Nenhuma pergunta cadastrada"
        )

    else:

        for pergunta in perguntas:

            with st.container(border=True):

                st.write(
                    pergunta["enunciado"]
                )

                st.write(
                    f"Dificuldade: {pergunta['nivel']}"
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "Editar",
                        key=f"editar_{pergunta['id']}"
                    ):

                        st.session_state.id_pergunta = (
                            pergunta["id"]
                        )

                        st.session_state.pagina = (
                            "editar_pergunta"
                        )

                        st.rerun()

                with col2:

                    if st.button(
                        "Excluir",
                        key=f"excluir_{pergunta['id']}"
                    ):

                        st.session_state.id_pergunta = (
                            pergunta["id"]
                        )

                        st.session_state.pagina = (
                            "excluir_pergunta"
                        )

                        st.rerun()

    st.divider()

    if st.button("Voltar"):

        st.session_state.pagina = (
            "mini_provas"
        )

        st.rerun()
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
