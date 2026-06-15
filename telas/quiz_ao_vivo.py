import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho

from services.quiz_ao_vivo_service import (
    criar_quiz,
    adicionar_pergunta,
    alterar_status_quiz,
    entrar_quiz,
    obter_perguntas_quizaovivo,
    responder_pergunta,
    obter_ranking,
    avancar_pergunta,
    repo_get_quiz,
)


def tela_quiz_ao_vivo():
    aplicar_estilo()

    usuario = st.session_state.get("usuario_logado", {})
    tipo = usuario.get("tipo_usuario", "aluno")

    cabecalho(
        "Quiz ao Vivo",
        "Responda as perguntas em tempo real ou gerencie as rodadas ativas"
    )

    if tipo == "professor":
        st.subheader("Criar Quiz")

        titulo = st.text_input("Titulo do Quiz")

        if st.button("Criar Quiz", use_container_width=True):
            resultado = criar_quiz(titulo, usuario.get("id"))

            if resultado["sucesso"]:
                # Exibe o UUID gerado pelo banco para o professor poder copiar
                quiz_criado = resultado["dados"]
                st.success(f"Quiz criado com sucesso! ID do Quiz (UUID): {quiz_criado.get('id')}")
            else:
                st.error(resultado["mensagem"])

        st.subheader("Adicionar Pergunta")

        # ✅ Trocado para text_input para aceitar chaves UUID
        quiz_id = st.text_input(
            "ID do Quiz (Cole o UUID)",
            key="quiz_pergunta",
            placeholder="Ex: 123e4567-e89b-12d3-a456-426614174000"
        )

        texto = st.text_area("Pergunta")

        alt1 = st.text_input("Alternativa A")
        alt2 = st.text_input("Alternativa B")
        alt3 = st.text_input("Alternativa C")
        alt4 = st.text_input("Alternativa D")

        alternativas = [alt1, alt2, alt3, alt4]

        letra_correta = st.selectbox(
            "Alternativa Correta",
            ["A", "B", "C", "D"],
        )

        mapa = {"A": 0, "B": 1, "C": 2, "D": 3}
        indice = mapa[letra_correta]

        if st.button("Adicionar Pergunta", use_container_width=True):
            if not quiz_id:
                st.warning("Por favor, insira o ID UUID do quiz.")
            else:
                resultado = adicionar_pergunta(
                    quiz_id,
                    usuario.get("id"),
                    texto,
                    alternativas,
                    indice,
                )

                if resultado["sucesso"]:
                    st.success("Pergunta adicionada com sucesso ao Quiz!")
                else:
                    st.error(resultado["mensagem"])

        st.subheader("Controlar Quiz")

        # ✅ Trocado para text_input para aceitar chaves UUID
        quiz_id_controle = st.text_input(
            "Quiz para controlar (Cole o UUID)",
            key="quiz_controle",
            placeholder="Ex: 123e4567-e89b-12d3-a456-426614174000"
        )

        col_iniciar, col_proxima, col_finalizar = st.columns(3)

        with col_iniciar:
            if st.button("Iniciar Quiz", use_container_width=True):
                if not quiz_id_controle:
                    st.error("Informe o UUID do Quiz")
                else:
                    resultado = alterar_status_quiz(
                        quiz_id_controle,
                        usuario.get("id"),
                        "iniciado",
                    )

                    if resultado["sucesso"]:
                        st.success("Quiz iniciado!")
                        st.rerun()
                    else:
                        st.error(resultado["mensagem"])

        with col_proxima:
            if st.button("Proxima Pergunta", use_container_width=True):
                if not quiz_id_controle:
                    st.error("Informe o UUID do Quiz")
                else:
                    resultado = avancar_pergunta(
                        quiz_id_controle,
                        usuario.get("id")
                    )

                    if resultado["sucesso"]:
                        pergunta_atual = resultado["dados"].get("pergunta_atual")
                        st.success(f"Pergunta atual (Índice): {pergunta_atual}")
                        st.rerun()
                    else:
                        st.error(resultado["mensagem"])

        with col_finalizar:
            if st.button("Finalizar Quiz", use_container_width=True):
                if not quiz_id_controle:
                    st.error("Informe o UUID do Quiz")
                else:
                    resultado = alterar_status_quiz(
                        quiz_id_controle,
                        usuario.get("id"),
                        "finalizado",
                    )

                    if resultado["sucesso"]:
                        st.success("Quiz finalizado!")
                        st.rerun()
                    else:
                        st.error(resultado["mensagem"])

        if quiz_id_controle:
            quiz = repo_get_quiz(quiz_id_controle)
            if quiz:
                st.markdown(f"""
                <div style="
                    background: #f0f9ff;
                    border-left: 4px solid #00b4d8;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-top: 15px;
                ">
                    <span style="color: #0d1b2a; font-weight: 600;">Status Atual: {quiz.get('status', '-')}</span><br>
                    <span style="color: #555; font-size: 13px;">Pergunta Atual (Indice): {quiz.get('pergunta_atual', '-')}</span>
                </div>
                """, unsafe_allow_html=True)

    else:
        # ✅ Painel do Aluno ajustado para receber UUID em texto
        quiz_id = st.text_input(
            "ID do Quiz fornecido pelo Professor (Cole o UUID)",
            key="quiz_aluno",
            placeholder="Ex: 123e4567-e89b-12d3-a456-426614174000"
        )

        if st.button("Entrar no Quiz", use_container_width=True):
            if not quiz_id:
                st.warning("Insira o ID do Quiz para entrar.")
            else:
                resultado = entrar_quiz(usuario.get("id"), quiz_id)

                if resultado["sucesso"]:
                    st.session_state[f"participacao_quiz_{quiz_id}"] = (
                        resultado["dados"]["id"]
                    )
                    st.success("Voce entrou no quiz com sucesso!")
                    st.rerun()
                else:
                    st.error(resultado["mensagem"])

        if quiz_id:
            st.button("Atualizar pergunta", key=f"atualizar_quiz_{quiz_id}", use_container_width=True)
            participacao_id = st.session_state.get(f"participacao_quiz_{quiz_id}")

            if participacao_id:
                quiz = repo_get_quiz(quiz_id)

                if not quiz:
                    st.error("Quiz nao encontrado.")
                    st.stop()

                if quiz.get("status") == "finalizado":
                    st.success("Quiz encerrado!")
                    _mostrar_ranking(quiz_id)
                    st.stop()

                pergunta_atual = quiz.get("pergunta_atual")

                if quiz.get("status") != "iniciado" or pergunta_atual is None:
                    st.info("Aguardando o professor iniciar o quiz.")
                    st.stop()

                resultado = obter_perguntas_quizaovivo(quiz_id)

                if not resultado["sucesso"]:
                    st.error(resultado.get("mensagem", "Erro ao carregar perguntas"))
                    st.stop()

                perguntas = resultado["dados"]
                indice_atual = int(pergunta_atual)

                if indice_atual < 0 or indice_atual >= len(perguntas):
                    st.success("Quiz encerrado!")
                    _mostrar_ranking(quiz_id)
                    st.stop()

                pergunta = perguntas[indice_atual]
                alternativas = pergunta.get("alternativas") or []

                if not alternativas:
                    st.error("Pergunta sem alternativas.")
                    st.stop()

                st.subheader(f"Pergunta {indice_atual + 1} de {len(perguntas)}")

                escolha = st.radio(
                    pergunta["texto"],
                    alternativas,
                    key=f"quiz_{quiz_id}_pergunta_{pergunta['id']}",
                )

                if st.button("Responder", key=f"resp_{quiz_id}_{pergunta['id']}", use_container_width=True):
                    indice_resposta = alternativas.index(escolha)

                    retorno = responder_pergunta(
                        participacao_id,
                        pergunta["id"],
                        indice_resposta,
                    )

                    if retorno["sucesso"]:
                        st.success(retorno["dados"]["feedback"])
                        st.info(f"Sua pontuacao: {retorno['dados']['pontuacao']} pontos")
                    else:
                        st.error(retorno["mensagem"])

        st.divider()

    # ✅ Painel de Ranking ajustado para receber UUID em texto
    quiz_ranking = st.text_input(
        "Ver Ranking de um Quiz (Cole o UUID)",
        key="ranking",
        placeholder="Ex: 123e4567-e89b-12d3-a456-426614174000"
    )

    if st.button("Ver Ranking", use_container_width=True):
        if not quiz_ranking:
            st.warning("Insira o ID do Quiz para ver o ranking.")
        else:
            _mostrar_ranking(quiz_ranking)


def _mostrar_ranking(quiz_id):
    resultado = obter_ranking(quiz_id)

    if resultado["sucesso"]:
        st.subheader("Ranking")
        if not resultado["dados"]:
            st.info("Nenhum participante respondeu este quiz ainda.")
            return

        for posicao, jogador in enumerate(resultado["dados"], start=1):
            usuario_dados = jogador.get("usuarios") or {}
            nome = usuario_dados.get("nome", "Aluno")

            st.write(
                f"**{posicao}º lugar** - {nome} - {jogador['pontuacao']} pontos"
            )
    else:
        st.error(resultado["mensagem"])