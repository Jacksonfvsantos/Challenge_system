import streamlit as st
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

def tela_desempenho_mini_provas():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    nome_aluno = usuario.get("nome", "Estudante")
    
    cabecalho("📊 Meu Desempenho Acadêmico", "Acompanhe sua evolução e estatísticas gerais de mini-provas")

    if not usuario_id:
        st.error("Sessão de usuário inválida.")
        return

    # 🔍 BUSCA LOGS DE DESEMPENHO NO SUPABASE (historico_provas)
    try:
        res = supabase.table("historico_provas")\
            .select("nota, pontuacao, data_realizacao")\
            .eq("usuario_id", usuario_id)\
            .execute()
        logs = res.data or []
    except Exception as e:
        st.error(f"Erro ao conectar com a base de dados de performance: {e}")
        logs = []

    # ⚠️ REQUISITO: Tratamento caso o aluno não tenha feito nenhuma mini-prova
    if not logs:
        st.warning(f"👋 Olá, {nome_aluno}! Você ainda não realizou nenhuma mini-prova neste semestre.")
        st.info("💡 Assim que você concluir sua primeira avaliação ativa, seus gráficos de evolução, médias acadêmicas e histórico de XP acumulado aparecerão consolidados neste painel.")
        
        st.divider()
        if st.button("⬅️ Voltar para o Painel de Provas", use_container_width=True):
            st.session_state.pagina = "mini_provas"
            st.rerun()
        return

    # 📈 CALCULO DOS INDICADORES SE HOUVER DADOS
    total_provas = len(logs)
    notas = [float(item["nota"]) for item in logs]
    total_xp = sum([float(item["pontuacao"]) for item in logs])
    
    media_geral = sum(notas) / total_provas if total_provas > 0 else 0.0
    maior_nota = max(notas) if notas else 0.0

    # 🎛️ Bloco de Métricas Superiores
    st.markdown(f"### 🎯 Resumo de Conquistas de {nome_aluno}")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("📝 Provas Feitas", f"{total_provas}")
    col2.metric("📊 Média Geral", f"{media_geral:.1f}")
    col3.metric("🔥 Maior Nota", f"{maior_nota:.1f}")
    col4.metric("⭐ Total XP", f"+{total_xp:.2f} pts")

    st.divider()

    # 📉 Gráfico Prático de Evolução usando o componente nativo do Streamlit
    st.markdown("### 📈 Curva de Evolução Temporal")
    st.caption("Acompanhe a oscilação das suas notas ao longo das tentativas realizadas.")
    
    # Inverte a ordem para exibir cronologicamente da mais antiga para a mais recente no gráfico
    historico_grafico = list(reversed(notas))
    st.line_chart(historico_grafico)

    st.divider()

    # 🏅 Mensagem de Feedback Motivacional com base na média
    if media_geral >= 7.0:
        st.success("🚀 Excelente rendimento! Suas métricas indicam ótimo domínio dos tópicos avaliados. Continue mantendo o foco nos próximos simulados!")
    elif media_geral >= 5.0:
        st.info("📈 Bom progresso! Você está na média de aprovação, mas revisando os gabaritos detalhados no histórico poderá alcançar notas ainda maiores.")
    else:
        st.warning("⚠️ Atenção necessária! Suas notas atuais estão abaixo da linha de corte recomendada. Utilize o painel de histórico para revisar os enunciados errados.")

    # Botão de retorno
    if st.button("⬅️ Voltar para as Mini Provas", use_container_width=True, type="secondary"):
        st.session_state.pagina = "mini_provas"
        st.rerun()