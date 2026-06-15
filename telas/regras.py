import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho

def tela_central_regras():
    aplicar_estilo()

    cabecalho(
        "📖 Manual da Plataforma e Regras de Conduta",
        "Consulte os objetivos de cada módulo, critérios de pontuação e diretrizes de Fair Play."
    )

    # Organização das telas sugeridas por abas limpas (Itens 6.90 e 7.152)
    aba_geral, aba_desafios, aba_provas, aba_quiz, aba_batalhas = st.tabs([
        "🛡️ Diretrizes Gerais",
        "🎯 1. Desafios",
        "📝 2. Mini-Provas",
        "🎮 3. Quiz ao Vivo",
        "⚔️ 4. Batalha em Equipe"
    ])

    # --- ABA 0: DIRETRIZES GERAIS ---
    with aba_geral:
        st.subheader("Código de Ética e Fair Play")
        st.write("""
        A nossa plataforma foi idealizada para fomentar o aprendizado colaborativo e a evolução prática ativa. 
        Para garantir um ambiente saudável, todos os participantes devem seguir as regras abaixo:
        """)
        with st.container(border=True):
            st.markdown("""
            - 🚫 **Plágio:** É terminantemente proibido submeter códigos copiados de colegas ou de repositórios externos sem a devida atribuição de créditos.
            - 🤝 **Colaboração:** Ajude seus pares nos fóruns e chats, mas permita que eles desenvolvam a lógica de seus próprios códigos.
            - 🔒 **Segurança:** Tentativas de burlar as travas de tempo ou requisições do sistema serão reportadas diretamente à coordenação do curso.
            """)

    # --- ABA 1: DESAFIOS ---
    with aba_desafios:
        st.subheader("Módulo de Desafios Acadêmicos")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("**🎯 Objetivo do Módulo**")
                st.write("Estimular a resolução de problemas reais de engenharia e programação por meio de desafios propostos pelo corpo docente.")
        with col2:
            with st.container(border=True):
                st.markdown("**⚙️ Regras de Funcionamento**")
                st.write("Os alunos devem ler o enunciado, desenvolver a solução localmente e submeter o projeto dentro do prazo estipulado pelo professor.")

        with st.container(border=True):
            st.markdown("**⭐ Critérios de Pontuação e Votação**")
            st.markdown("""
            - A avaliação é feita de forma **paritária (pelos próprios colegas)** no painel de votação.
            - Cada aluno pode atribuir uma nota de **1 a 10** baseada em critérios de: *Lógica, Organização e Criatividade*.
            - As melhores pontuações do ranking convertem-se em vantagens no sistema de recompensas.
            """)

    # --- ABA 2: MINI-PROVAS ---
    with aba_provas:
        st.subheader("Módulo de Mini-Provas (Quiz Assíncrono)")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("**🎯 Objetivo do Módulo**")
                st.write("Avaliar a retenção de conceitos teóricos e práticos de disciplinas específicas de forma rápida e modular.")
        with col2:
            with st.container(border=True):
                st.markdown("**⚙️ Regras de Funcionamento**")
                st.write("As mini-provas possuem tempo de duração controlado em minutos e quantidade fixa de questões de múltipla escolha.")

        with st.container(border=True):
            st.markdown("**⭐ Critérios de Pontuação**")
            st.markdown("""
            - Cada questão respondida corretamente concede **1 ponto** na nota base da avaliação.
            - O envio é finalizado automaticamente caso o cronômetro estoure o tempo limite configurado.
            """)

    # --- ABA 3: QUIZ AO VIVO ---
    with aba_quiz:
        st.subheader("Módulo de Quiz ao Vivo (Síncrono)")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("**🎯 Objetivo do Módulo**")
                st.write("Promover a gamificação síncrona em sala de aula, revisando conteúdos antes de avaliações majoritárias.")
        with col2:
            with st.container(border=True):
                st.markdown("**⚙️ Regras de Funcionamento**")
                st.write("Os alunos ingressam na sala digitando ou selecionando o quiz iniciado. As perguntas avançam conforme o comando do professor no telão.")

        with st.container(border=True):
            st.markdown("**⭐ Critérios de Pontuação**")
            st.markdown("""
            - Cada resposta correta adiciona **+10 pontos** imediatos ao score do aluno no Quiz.
            - Respostas incorretas não deduzem pontos.
            - O ranking atualiza em tempo real a cada rodada enviada para o telão.
            """)

    # --- ABA 4: BATALHA EM EQUIPE ---
    with aba_batalhas:
        st.subheader("Módulo de Batalhas de Engenharia")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("**🎯 Objetivo do Módulo**")
                st.write("Fomentar o desenvolvimento de software em equipe e a resolução de maratonas de programação (Hackatons internos).")
        with col2:
            with st.container(border=True):
                st.markdown("**⚙️ Regras de Funcionamento**")
                st.write("Professores lançam batalhas futuras com regras de segurança estritas. Os alunos devem se organizar em equipes para competir.")

        with st.container(border=True):
            st.markdown("**⭐ Critérios de Pontuação**")
            st.markdown("""
            - A equipe que concluir o maior número de rodadas corretas dentro do tempo limite vence a batalha.
            - São auditados logs de segurança IP e submissões para validar o resultado oficial divulgado pelo professor.
            """)
            
        st.divider()
        st.caption("❓ Tem alguma dúvida adicional? Procure o professor responsável pela disciplina ou o administrador do sistema.")