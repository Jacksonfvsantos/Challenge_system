import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho

def tela_batalha_de_equipes():
    aplicar_estilo()

    usuario = st.session_state.get("usuario_logado", {})
    nome = usuario.get("nome", "Usuário")
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()

    cabecalho(
        "⚔️ Arena de Batalhas de Equipes",
        "Participe de maratonas de programação, resolva rodadas de engenharia e gerencie seus times"
    )

    # Info Card explicativo da dinâmica
    with st.container(border=True):
        st.markdown("### 🗺️ O que você deseja fazer?")
        st.write("Selecione uma das opções abaixo para navegar pelas ferramentas do módulo de competições:")

    st.markdown("<br>", unsafe_allow_html=True)

    # Layout de Grade de Botões de Navegação do Módulo
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### 👥 Integrantes e Times")
            st.write("Consulte a formação oficial das equipes da turma ou gerencie as alocações de estudantes.")
            if st.button("👁️ Ver Membros por Equipe", use_container_width=True):
                st.session_state.pagina = "batalha_integrantes"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("#### 🛡️ Manual e Regras")
            st.write("Confira as diretrizes de conduta, critérios de avaliação e o regulamento de Fair Play.")
            if st.button("📖 Ler Regras da Arena", use_container_width=True):
                st.session_state.pagina = "batalha_regras"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # SEÇÃO EXCLUSIVA: Painel Administrativo do Professor
    if tipo in ("professor", "admin"):
        st.divider()
        st.markdown("### ⚙️ Painel de Controle Docente")
        
        col3, col4 = st.columns(2)
        
        with col3:
            with st.container(border=True):
                st.markdown("#### 🏁 Gerenciar Equipes")
                st.write("Crie novos times na tabela unificada, edite nomenclaturas ou remova registros.")
                if st.button("🛠️ Abrir Gestão de Times", type="secondary", use_container_width=True):
                    st.session_state.pagina = "batalha_times"
                    st.rerun()
                    
        with col4:
            with st.container(border=True):
                st.markdown("#### ⚔️ Lançar e Encerrar Batalhas")
                st.write("Publique novos desafios competitivos com prazos limites e configurações de segurança.")
                if st.button("➕ Nova Batalha Síncrona", type="primary", use_container_width=True):
                    st.session_state.pagina = "batalha_gerenciar"
                    st.rerun()

    else:
        st.divider()
        st.markdown("### 🕹️ Painel de Jogador")
        
        col_aluno1, col_aluno2 = st.columns(2)
        with col_aluno1:
            with st.container(border=True):
                st.markdown("#### 🚀 Competir")
                if st.button("Entrar na Rodada Ativa", type="primary", use_container_width=True):
                    st.session_state.pagina = "batalha_rodada"
                    st.rerun()
                    
        with col_aluno2:
            with st.container(border=True):
                st.markdown("#### 🌟 Minha Equipe")
                # LIBERADO O ACESSO À TELA DE TIMES PARA O ALUNO CRIER SEU TIME
                if st.button("Fundar ou Entrar em um Time", use_container_width=True):
                    st.session_state.pagina = "batalha_times"
                    st.rerun()