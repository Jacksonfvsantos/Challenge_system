import streamlit as st
<<<<<<< HEAD
from services.mini_prova_service import criar_pergunta
from utils.estilo import aplicar_estilo, cabecalho

def tela_cadastro_perguntas():
    aplicar_estilo()
    
    cabecalho(
        "Cadastro de Questões", 
        "Alimente o banco de dados de mini-provas criando novas perguntas de múltipla escolha"
    )

    # Inicialização das chaves de controle de estado para permitir a limpeza do formulário (Item Geral 9)
    campos = ["cp_disp", "cp_ass", "cp_enun", "cp_alt_a", "cp_alt_b", "cp_alt_c", "cp_alt_d", "cp_alt_e"]
    for campo in campos:
        if campo not in st.session_state:
            st.session_state[campo] = ""

    with st.form("form_cadastro_pergunta_modular", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            disciplina = st.text_input("Disciplina acadêmica", value=st.session_state["cp_disp"], placeholder="Ex: Circuitos Digitais")
        with col2:
            assunto = st.text_input("Assunto / Tema", value=st.session_state["cp_ass"], placeholder="Ex: Portas Lógicas")

        dificuldade = st.selectbox("Nível de Complexidade", ["facil", "intermediario", "dificil"])
        pergunta = st.text_area("Enunciado da Questão", value=st.session_state["cp_enun"], placeholder="Digite o texto da pergunta...")

        st.markdown("<p style='font-weight: bold; margin-top: 15px;'>Alternativas de Resposta</p>", unsafe_allow_html=True)
        alternativa_a = st.text_input("A)", value=st.session_state["cp_alt_a"])
        alternativas_b = st.text_input("B)", value=st.session_state["cp_alt_b"])
        alternativa_c = st.text_input("C)", value=st.session_state["cp_alt_c"])
        alternativa_d = st.text_input("D)", value=st.session_state["cp_alt_d"])
        alternativa_e = st.text_input("E)", value=st.session_state["cp_alt_e"])

        resposta_correta = st.selectbox("Gabarito Oficial (Alternativa Correta)", ["A", "B", "C", "D", "E"])

        st.markdown("<br>", unsafe_allow_html=True)
        btn_gravar = st.form_submit_button("Confirmar e Salvar Questão", use_container_width=True)

    if btn_gravar:
        if not disciplina or not pergunta or not alternativa_a or not alternativas_b:
            st.error("Preenchimento obrigatório: Disciplina, Enunciado e pelo menos duas alternativas (A e B).")
        else:
            usuario = st.session_state.usuario_logado
            dados = {
                "email_professor": usuario["email"],
                "disciplina": disciplina,
                "assunto": assunto,
                "enunciado": pergunta,
                "nivel": dificuldade,
                "alternativa_a": alternativa_a,
                "alternativa_b": alternativas_b,
                "alternativa_c": alternativa_c,
                "alternativa_d": alternativa_d,
                "alternativa_e": alternativa_e,
                "resposta_correta": resposta_correta
            }

            resultado = criar_pergunta(dados)

            if resultado["sucesso"]:
                st.success(f"✅ {resultado['mensagem']}")
                # Executa a limpeza completa dos estados na sessão
                for campo in campos:
                    st.session_state[campo] = ""
                st.rerun()
            else:
                # Feedback de erro amigável sem códigos complexos expostos (Item Geral 10)
                st.error(resultado["mensagem"])

    st.divider()
    if st.button("⬅️ Voltar para o Módulo de Mini-Provas", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()
=======

from services.mini_prova_service import (
    criar_pergunta
)


def tela_cadastro_perguntas():

    st.title("Cadastro de Perguntas")

    disciplina = st.text_input(
        "Disciplina"
    )

    assunto = st.text_input(
        "Assunto"
    )

    dificuldade = st.selectbox(
        "Dificuldade",
        [
            "facil",
            "intermediario",
            "dificil"
        ]
    )

    pergunta = st.text_area(
        "Pergunta"
    )

    st.subheader("Alternativas")

    alternativa_a = st.text_input(
        "Alternativa A"
    )

    alternativa_b = st.text_input(
        "Alternativa B"
    )

    alternativa_c = st.text_input(
        "Alternativa C"
    )

    alternativa_d = st.text_input(
        "Alternativa D"
    )

    alternativa_e = st.text_input(
        "Alternativa E"
    )

    resposta_correta = st.selectbox(
        "Resposta correta",
        [
            "A",
            "B",
            "C",
            "D",
            "E"
        ]
    )

    if st.button(
        "Cadastrar pergunta"
    ):

        usuario = (
            st.session_state.usuario_logado
        )

        dados = {

            "email_professor":
            usuario["email"],

            "disciplina":
            disciplina,

            "assunto":
            assunto,

            "enunciado":
            pergunta,

            "nivel":
            dificuldade,

            "alternativa_a":
            alternativa_a,

            "alternativa_b":
            alternativa_b,

            "alternativa_c":
            alternativa_c,

            "alternativa_d":
            alternativa_d,

            "alternativa_e":
            alternativa_e,

            "resposta_correta":
            resposta_correta
        }

        criar_pergunta(dados)

        st.success(
            "Pergunta cadastrada"
        )

    st.divider()

    if st.button("Voltar"):

        st.session_state.pagina = (
            "mini_provas"
        )

        st.rerun()
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
