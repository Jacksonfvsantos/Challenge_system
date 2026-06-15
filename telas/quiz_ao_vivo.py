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
    listar_quizzes_professor,  # <-- Nova função importada
)


def tela_quiz_ao_vivo():
    aplicar_estilo()

    usuario = st.session_state.get("usuario_logado", {})
    tipo = usuario.get("tipo_usuario", "aluno")

    cabecalho(
        "Quiz ao Vivo",
        "Responda as perguntas em tempo real ou gerencie as rodadas ativas"
    )

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
            key="quiz_aluno",
            placeholder="Ex: 123e4567-e89b-12d3-a456-426614174000"
        )

        if st.button("Ingressar na Sala do Quiz", use_container_width=True):
            if not quiz_id:
                st.warning("Insira um código de acesso válido.")
            else:
                resultado = entrar_quiz(usuario.get("id"), quiz_id)
                if resultado["sucesso"]:
                    st.session_state[f"participacao_quiz_{quiz_id}"] = resultado["dados"]["id"]
                    st.success("Acesso autorizado! Sincronizando com o painel do professor...")
                    st.rerun()
                else:
                    st.error(resultado["mensagem"])

        if quiz_id and _eh_uuid_valido(quiz_id):
            st.button("🔄 Sincronizar / Atualizar Pergunta", key=f"atualizar_quiz_{quiz_id}", use_container_width=True)
            participacao_id = st.session_state.get(f"participacao_quiz_{quiz_id}")

            if participacao_id:
                quiz = repo_get_quiz(quiz_id)

                if not quiz:
                    st.error("Quiz não localizado no servidor.")
                    st.stop()

                if quiz.get("status") == "finalizado":
                    st.success("🏁 O tempo acabou! Este quiz foi encerrado pelo professor.")
                    _mostrar_ranking(quiz_id)
                    st.stop()

                pergunta_atual = quiz.get("pergunta_atual")

                if quiz.get("status") != "iniciado" or pergunta_atual is None:
                    st.info("⌛ Sala de espera: Aguardando o comando do professor para liberar a primeira questão.")
                    st.stop()

                resultado = obter_perguntas_quizaovivo(quiz_id)
                if not resultado["sucesso"]:
                    st.error(resultado.get("mensagem", "Erro ao carregar perguntas"))
                    st.stop()

                perguntas = resultado["dados"]
                indice_atual = int(pergunta_atual)

                if indice_atual < 0 or indice_atual >= len(perguntas):
                    st.success("🏁 Parabéns! Você concluiu todas as questões enviadas.")
                    _mostrar_ranking(quiz_id)
                    st.stop()

                pergunta = perguntas[indice_atual]
                alternativas = pergunta.get("alternativas") or []

                if not alternativas:
                    st.error("Esta questão não possui alternativas configuradas.")
                    st.stop()

                st.subheader(f"Questão {indice_atual + 1} de {len(perguntas)}")

                escolha = st.radio(
                    pergunta["texto"],
                    alternativas,
                    key=f"quiz_{quiz_id}_pergunta_{pergunta['id']}",
                )

                if st.button("Enviar Resposta", key=f"resp_{quiz_id}_{pergunta['id']}", use_container_width=True):
                    indice_resposta = alternativas.index(escolha)
                    retorno = responder_pergunta(participacao_id, pergunta["id"], indice_resposta)

                    if retorno["sucesso"]:
                        st.success(retorno["dados"]["feedback"])
                        st.info(f"Painel de Resultados: {retorno['dados']['pontuacao']} pontos acumulados.")
                    else:
                        st.error(retorno["mensagem"])

        st.divider()

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
        else:
            _mostrar_ranking(quiz_ranking)


def _mostrar_ranking(quiz_id):
    resultado = obter_ranking(quiz_id)

    if resultado["sucesso"]:
        st.subheader("🏆 Placar de Líderes")
        if not resultado["dados"]:
            st.info("Nenhum registro encontrado. Nenhum aluno respondeu a este quiz até o momento.")
            return

        for posicao, jogador in enumerate(resultado["dados"], start=1):
            usuario_dados = jogador.get("usuarios") or {}
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