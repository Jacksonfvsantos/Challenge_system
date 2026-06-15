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
<<<<<<< HEAD
    listar_quizzes_professor,  # <-- Nova função importada
=======
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
)


def tela_quiz_ao_vivo():
    aplicar_estilo()

    usuario = st.session_state.get("usuario_logado", {})
    tipo = usuario.get("tipo_usuario", "aluno")

    cabecalho(
        "Quiz ao Vivo",
        "Responda as perguntas em tempo real ou gerencie as rodadas ativas"
    )

<<<<<<< HEAD
    # 📥 BUSCA PRÉVIA DE QUIZZES (Para evitar que o professor precise adivinhar ou digitar IDs)
    quizzes_professor = []
    mapa_quizzes = {}
    if tipo == "professor":
        quizzes_professor = listar_quizzes_professor(usuario.get("id"))
        mapa_quizzes = {q["titulo"]: q["id"] for q in quizzes_professor}

    if tipo == "professor":
        # Organização por abas estruturadas (Sugerido no relatório para evitar rolagem excessiva)
        aba_criar, aba_perguntas, aba_controle = st.tabs([
            "✨ Criar Novo Quiz", 
            "📝 Adicionar Perguntas", 
            "🎮 Painel de Controle (Telão)"
        ])

        # 🚀 ABA 1: CRIAR QUIZ (Atualizada com Disciplina e Temas)
        with aba_criar:
            st.subheader("Configurações Iniciais")
            
            if "input_titulo_quiz" not in st.session_state: st.session_state["input_titulo_quiz"] = ""
            if "input_disc_quiz" not in st.session_state: st.session_state["input_disc_quiz"] = ""
            if "input_tema_quiz" not in st.session_state: st.session_state["input_tema_quiz"] = ""

            titulo = st.text_input(
                "Título do Quiz", 
                value=st.session_state["input_titulo_quiz"],
                placeholder="Ex: Simulado de Redes de Computadores"
            )
            
            # NOVOS CAMPOS EXIGIDOS NO RELATÓRIO (Itens 4.74 e 4.75)
            col_d, col_t = st.columns(2)
            with col_d:
                disciplina_input = st.text_input(
                    "Disciplina Associada", 
                    value=st.session_state["input_disc_quiz"],
                    placeholder="Ex: Engenharia de Software"
                )
            with col_t:
                tema_input = st.text_input(
                    "Assunto / Tema Principal", 
                    value=st.session_state["input_tema_quiz"],
                    placeholder="Ex: Arquitetura REST"
                )

            if st.button("Gravar e Ativar Quiz", use_container_width=True):
                if not titulo:
                    st.warning("Por favor, forneça um título válido.")
                else:
                    # Envia os novos parâmetros para o serviço
                    resultado = criar_quiz(titulo, usuario.get("id"), disciplina_input, tema_input)
                    if resultado["sucesso"]:
                        st.success(f"✅ {resultado['mensagem']} | ID Gerado: {resultado['dados'].get('id')}")
                        
                        # Limpa todos os campos do formulário após o sucesso (Item Geral 9)
                        st.session_state["input_titulo_quiz"] = ""
                        st.session_state["input_disc_quiz"] = ""
                        st.session_state["input_tema_quiz"] = ""
                        st.rerun()
                    else:
                        st.error(resultado["mensagem"])

        # 📝 ABA 2: ADICIONAR PERGUNTAS
        with aba_perguntas:
            st.subheader("Nova Pergunta")
            
            if not mapa_quizzes:
                st.info("Você precisa criar pelo menos um Quiz antes de adicionar perguntas.")
            else:
                # CORREÇÃO CRÍTICA: Seleção por Nome em vez de ID Técnico
                quiz_selecionado_nome = st.selectbox(
                    "Selecione o Quiz Destino",
                    options=list(mapa_quizzes.keys()),
                    key="sb_quiz_pergunta"
                )
                quiz_id = mapa_quizzes[quiz_selecionado_nome]

                texto = st.text_area("Enunciado da Pergunta", placeholder="Digite a questão aqui...")

                alt1 = st.text_input("Alternativa A", key="alt_a")
                alt2 = st.text_input("Alternativa B", key="alt_b")
                alt3 = st.text_input("Alternativa C", key="alt_c")
                alt4 = st.text_input("Alternativa D", key="alt_d")

                letra_correta = st.selectbox("Gabarito Oficial", ["A", "B", "C", "D"])
                mapa_letras = {"A": 0, "B": 1, "C": 2, "D": 3}
                indice = mapa_letras[letra_correta]

                if st.button("Salvar Pergunta", use_container_width=True):
                    alternativas = [alt1, alt2, alt3, alt4]
                    resultado = adicionar_pergunta(quiz_id, usuario.get("id"), texto, alternativas, indice)

                    if resultado["sucesso"]:
                        st.success("✅ Pergunta vinculada e salva com sucesso!")
                        st.rerun()
                    else:
                        st.error(resultado["mensagem"])

        # 🎮 ABA 3: CONTROLAR QUIZ (Atualizada com mensagens de status explícitas)
        with aba_controle:
            st.subheader("Gerenciador de Rodadas Online")
            
            if not mapa_quizzes:
                st.info("Nenhum quiz disponível para controle remoto.")
            else:
                quiz_controle_nome = st.selectbox(
                    "Qual quiz deseja comandar no telão?",
                    options=list(mapa_quizzes.keys()),
                    key="sb_quiz_controle"
                )
                quiz_id_controle = mapa_quizzes[quiz_controle_nome]

                col_iniciar, col_proxima, col_finalizar = st.columns(3)

                with col_iniciar:
                    if st.button("▶️ Iniciar Rodada", use_container_width=True):
                        resultado = alterar_status_quiz(quiz_id_controle, usuario.get("id"), "iniciado")
                        if resultado["sucesso"]:
                            # Mensagem clara de operação (Item 4.84)
                            st.toast("⚡ Operação realizada: O quiz mudou de status para INICIADO!")
                            st.success("O quiz foi aberto! Alunos já podem responder em tempo real.")
                            st.rerun()
                        else:
                            st.error(resultado["mensagem"])

                with col_proxima:
                    if st.button("⏭️ Próxima Pergunta", use_container_width=True):
                        resultado = avancar_pergunta(quiz_id_controle, usuario.get("id"))
                        if resultado["sucesso"]:
                            st.toast("📑 Operação realizada: Comando de avançar enviado!")
                            st.success("Avançado com sucesso para a próxima questão!")
                            st.rerun()
                        else:
                            st.error(resultado["mensagem"])

                with col_finalizar:
                    if st.button("🛑 Encerrar Quiz", use_container_width=True):
                        resultado = alterar_status_quiz(quiz_id_controle, usuario.get("id"), "finalizado")
                        if resultado["sucesso"]:
                            # Mensagem clara de encerramento exigida (Item 4.84)
                            st.toast("🛑 Operação realizada: O quiz mudou de status para FINALIZADO!")
                            st.success("Quiz finalizado com sucesso! Histórico de ranking consolidado para a banca.")
                            st.rerun()
                        else:
                            st.error(resultado["mensagem"])

    # 👨‍🎓 PAINEL DO ALUNO
    else:
        # Nota: O aluno ainda pode precisar colar o ID compartilhado via QR Code/Link ou você pode listar os iniciados do banco.
        quiz_id = st.text_input(
            "Insira o código do Quiz ativo (UUID fornecido pelo professor)",
=======
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
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
            key="quiz_aluno",
            placeholder="Ex: 123e4567-e89b-12d3-a456-426614174000"
        )

<<<<<<< HEAD
        if st.button("Ingressar na Sala do Quiz", use_container_width=True):
            if not quiz_id:
                st.warning("Insira um código de acesso válido.")
            else:
                resultado = entrar_quiz(usuario.get("id"), quiz_id)
                if resultado["sucesso"]:
                    st.session_state[f"participacao_quiz_{quiz_id}"] = resultado["dados"]["id"]
                    st.success("Acesso autorizado! Sincronizando com o painel do professor...")
=======
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
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
                    st.rerun()
                else:
                    st.error(resultado["mensagem"])

<<<<<<< HEAD
        if quiz_id and _eh_uuid_valido(quiz_id):
            st.button("🔄 Sincronizar / Atualizar Pergunta", key=f"atualizar_quiz_{quiz_id}", use_container_width=True)
=======
        if quiz_id:
            st.button("Atualizar pergunta", key=f"atualizar_quiz_{quiz_id}", use_container_width=True)
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
            participacao_id = st.session_state.get(f"participacao_quiz_{quiz_id}")

            if participacao_id:
                quiz = repo_get_quiz(quiz_id)

                if not quiz:
<<<<<<< HEAD
                    st.error("Quiz não localizado no servidor.")
                    st.stop()

                if quiz.get("status") == "finalizado":
                    st.success("🏁 O tempo acabou! Este quiz foi encerrado pelo professor.")
=======
                    st.error("Quiz nao encontrado.")
                    st.stop()

                if quiz.get("status") == "finalizado":
                    st.success("Quiz encerrado!")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
                    _mostrar_ranking(quiz_id)
                    st.stop()

                pergunta_atual = quiz.get("pergunta_atual")

                if quiz.get("status") != "iniciado" or pergunta_atual is None:
<<<<<<< HEAD
                    st.info("⌛ Sala de espera: Aguardando o comando do professor para liberar a primeira questão.")
                    st.stop()

                resultado = obter_perguntas_quizaovivo(quiz_id)
=======
                    st.info("Aguardando o professor iniciar o quiz.")
                    st.stop()

                resultado = obter_perguntas_quizaovivo(quiz_id)

>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
                if not resultado["sucesso"]:
                    st.error(resultado.get("mensagem", "Erro ao carregar perguntas"))
                    st.stop()

                perguntas = resultado["dados"]
                indice_atual = int(pergunta_atual)

                if indice_atual < 0 or indice_atual >= len(perguntas):
<<<<<<< HEAD
                    st.success("🏁 Parabéns! Você concluiu todas as questões enviadas.")
=======
                    st.success("Quiz encerrado!")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
                    _mostrar_ranking(quiz_id)
                    st.stop()

                pergunta = perguntas[indice_atual]
                alternativas = pergunta.get("alternativas") or []

                if not alternativas:
<<<<<<< HEAD
                    st.error("Esta questão não possui alternativas configuradas.")
                    st.stop()

                st.subheader(f"Questão {indice_atual + 1} de {len(perguntas)}")
=======
                    st.error("Pergunta sem alternativas.")
                    st.stop()

                st.subheader(f"Pergunta {indice_atual + 1} de {len(perguntas)}")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e

                escolha = st.radio(
                    pergunta["texto"],
                    alternativas,
                    key=f"quiz_{quiz_id}_pergunta_{pergunta['id']}",
                )

<<<<<<< HEAD
                if st.button("Enviar Resposta", key=f"resp_{quiz_id}_{pergunta['id']}", use_container_width=True):
                    indice_resposta = alternativas.index(escolha)
                    retorno = responder_pergunta(participacao_id, pergunta["id"], indice_resposta)

                    if retorno["sucesso"]:
                        st.success(retorno["dados"]["feedback"])
                        st.info(f"Painel de Resultados: {retorno['dados']['pontuacao']} pontos acumulados.")
=======
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
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
                    else:
                        st.error(retorno["mensagem"])

        st.divider()

<<<<<<< HEAD
    # 📊 SEÇÃO COMPARTILHADA: VISUALIZAR RANKING
    st.subheader("📈 Consultar Resultados Históricos")
    quiz_ranking = st.text_input(
        "Insira o código do Quiz para visualizar o placar geral",
        key="ranking",
        placeholder="Cole o ID UUID do quiz aqui..."
    )

    if st.button("Carregar Tabela de Classificação", use_container_width=True):
        if not quiz_ranking:
            st.warning("Forneça o código identificador do quiz.")
=======
    # ✅ Painel de Ranking ajustado para receber UUID em texto
    quiz_ranking = st.text_input(
        "Ver Ranking de um Quiz (Cole o UUID)",
        key="ranking",
        placeholder="Ex: 123e4567-e89b-12d3-a456-426614174000"
    )

    if st.button("Ver Ranking", use_container_width=True):
        if not quiz_ranking:
            st.warning("Insira o ID do Quiz para ver o ranking.")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
        else:
            _mostrar_ranking(quiz_ranking)


def _mostrar_ranking(quiz_id):
    resultado = obter_ranking(quiz_id)

    if resultado["sucesso"]:
<<<<<<< HEAD
        st.subheader("🏆 Placar de Líderes")
        if not resultado["dados"]:
            st.info("Nenhum registro encontrado. Nenhum aluno respondeu a este quiz até o momento.")
=======
        st.subheader("Ranking")
        if not resultado["dados"]:
            st.info("Nenhum participante respondeu este quiz ainda.")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
            return

        for posicao, jogador in enumerate(resultado["dados"], start=1):
            usuario_dados = jogador.get("usuarios") or {}
<<<<<<< HEAD
            nome = usuario_dados.get("nome", "Participante Anônimo")
            st.write(f"**{posicao}º Lugar** — {nome} | ⭐ `{jogador['pontuacao']} pts`")
    else:
        st.error(resultado["mensagem"])

def _eh_uuid_valido(valor: str) -> bool:
    try:
        import uuid
        uuid.UUID(str(valor).strip())
        return True
    except ValueError:
        return False
=======
            nome = usuario_dados.get("nome", "Aluno")

            st.write(
                f"**{posicao}º lugar** - {nome} - {jogador['pontuacao']} pontos"
            )
    else:
        st.error(resultado["mensagem"])
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
