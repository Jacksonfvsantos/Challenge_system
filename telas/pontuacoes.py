import streamlit as st
import pandas as pd
from utils.estilo import aplicar_estilo, cabecalho
from services.pontuacao_service import obter_dashboard_pontuacao_aluno, obter_ranking_geral_alunos

def tela_pontuacoes():
    aplicar_estilo()

    usuario = st.session_state.get("usuario_logado", {})
    tipo = usuario.get("tipo_usuario", "aluno")
    usuario_id = str(usuario.get("id", ""))

    cabecalho(
        "🏆 Central de Pontuações e Recompensas",
        "Acompanhe o seu engajamento acadêmico e evolução nas trilhas práticas"
    )

    if tipo == "professor":
        aba_prof, aba_aluno = st.tabs(["📊 Ferramentas do Professor", "👁️ Visualizar como Aluno"])
    else:
        aba_aluno, = st.tabs(["🏅 Meu Desempenho"])

    # --- ABA: PROFESSOR (Acompanhamento e Auditoria) ---
    if tipo == "professor":
        with aba_prof:
            st.subheader("Ferramentas de Acompanhamento (Professor)")
            st.caption("Consulte o engajamento geral e audite a classificação de líderes da turma.")
            
            ranking = obter_ranking_geral_alunos()
            if not ranking:
                st.info("Nenhum registro de pontuação foi computado nas tabelas até o momento.")
            else:
                df_ranking = pd.DataFrame(ranking)
                
                # Filtro rápido para o professor auditar
                busca = st.text_input("🔍 Buscar estudante pelo nome:")
                if busca:
                    df_ranking = df_ranking[df_ranking["Nome"].str.contains(busca, case=False)]
                
                st.markdown("**Placar Geral de Líderes (Gamificação)**")
                st.dataframe(df_ranking, use_container_width=True, hide_index=True)

    # --- ABA: ALUNO (Dashboard de Indicadores Pessoais) ---
    with aba_aluno:
        st.subheader("Painel de Indicadores de Desempenho")
        
        dash = obter_dashboard_pontuacao_aluno(usuario_id)
        
        if not dash.get("sucesso"):
            st.error(dash.get("mensagem"))
        else:
            # 1. Cards com Indicadores em Destaque (Item 6.132)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("⭐ Pontuação Total", f"{dash['pontuacao_total']} pts")
            col2.metric("🎮 Quizzes ao Vivo", f"{dash['quiz']} pts")
            col3.metric("⚔️ Batalhas/Desafios", f"{dash['desafios']} pts")
            col4.metric("📝 Mini-Provas", f"{dash['provas']} pts")

            st.divider()

            # 2. Gráfico de Evolução ao Longo do Tempo (Item 6.133)
            st.markdown("### 📈 Gráfico de Evolução Temporal")
            st.caption("Acompanhe o crescimento do seu score acumulado ao longo das semanas de aula.")
            
            df_ev = pd.DataFrame(dash["evolucao"])
            st.line_chart(data=df_ev, x="Data", y="Points" if "Points" in df_ev.columns else "Pontos")

            # 3. Caixa de Incentivos e Recompensas (Item 6.139)
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("### 🎁 Sistema de Incentivos e Recompensas")
                st.write("Acumule pontos resolvendo as atividades propostas para desbloquear vantagens:")
                st.markdown("""
                - 🥉 **50 pontos:** Selo de Participante Ativo no perfil.
                - 🥈 **150 pontos:** Prorrogação de 24h em 1 entrega de Desafio futuro.
                - 🥇 **300 pontos:** Isenção da menor nota de Mini-Prova do semestre!
                """)