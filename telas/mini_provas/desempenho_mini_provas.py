import streamlit as st
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

def tela_desempenho_mini_provas():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    
    # ✅ CORRIGIDO: Limpeza absoluta de string para evitar falha na validação do perfil
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).strip().lower()
    nome_usuario = usuario.get("nome", "Usuário")
    
    if not usuario_id:
        st.error("Sessão de usuário inválida.")
        return

    # ============================================================================
    # 👑 VISÃO DO PROFESSOR: MONITORAMENTO DE ALUNOS MATRICULADOS
    # ============================================================================
    if tipo_usuario == "professor" or tipo_usuario == "docente":
        cabecalho("📊 Desempenho dos Alunos", "Monitore o rendimento das turmas e analise notas por avaliação")

        # 1. Carrega todas as mini-provas criadas por este professor
        try:
            res_provas = supabase.table("mini_provas")\
                .select("id, titulo")\
                .eq("criado_por", usuario_id)\
                .order("data_criacao", desc=True)\
                .execute()
            lista_provas = res_provas.data or []
        except Exception as e:
            st.error(f"Erro ao carregar mini-provas: {e}")
            lista_provas = []

        if not lista_provas:
            st.info("💡 Você ainda não possui nenhuma Mini-prova cadastrada no sistema.")
            if st.button("➕ Criar Primeira Mini-prova", use_container_width=True, type="primary"):
                st.session_state.pagina = "mini_provas_professor"
                st.rerun()
            return

        # Menu seletor de provas para análise de desempenho
        dict_provas = {p["titulo"]: p["id"] for p in lista_provas}
        prova_selecionada = st.selectbox("Selecione a Mini-prova para auditar:", list(dict_provas.keys()))
        prova_id_alvo = dict_provas[prova_selecionada]

        # 2. Busca o histórico de todos os alunos que responderam a essa prova específica
        try:
            res_historico = supabase.table("historico_provas")\
                .select("nota, pontuacao, data_realizacao, usuarios(nome, email)")\
                .eq("mini_prova_id", prova_id_alvo)\
                .order("nota", desc=True)\
                .execute()
            logs_turma = res_historico.data or []
        except Exception as e:
            st.error(f"Erro ao buscar notas da turma: {e}")
            logs_turma = []

        # Tratamento caso nenhum aluno tenha feito a prova selecionada
        if not logs_turma:
            st.warning(f"📋 A mini-prova '{prova_selecionada}' ainda não recebeu nenhuma tentativa de resolução dos alunos.")
            
            st.divider()
            if st.button("⬅️ Voltar para o Painel Geral", use_container_width=True):
                st.session_state.pagina = "mini_provas"
                st.rerun()
            return

        # 3. Processamento de Métricas Consolidadas da Turma
        total_respostas = len(logs_turma)
        notas_turma = [float(item["nota"]) for item in logs_turma]
        media_turma = sum(notas_turma) / total_respostas
        maior_nota_turma = max(notas_turma)

        st.markdown(f"### 🎯 Indicadores Gerais — {prova_selecionada}")
        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Alunos Avaliados", f"{total_respostas}")
        col2.metric("📊 Média Geral da Turma", f"{media_turma:.1f} / 10.0")
        col3.metric("🔥 Maior Nota Registrada", f"{maior_nota_turma:.1f}")

        st.divider()

        # 4. Tabela Estruturada de Alunos (Dataframe Limpo)
        st.markdown("### 📋 Listagem Nominal de Rendimento")
        st.caption("Alunos ordenados de forma decrescente pela nota obtida no exame.")

        dados_tabela = []
        for item in logs_turma:
            dados_aluno = item.get("usuarios", {}) or {}
            try:
                data_iso = item.get("data_realizacao", "")
                data_formatada = data_iso.split("T")[0] if "T" in data_iso else data_iso
            except:
                data_formatada = item.get("data_realizacao")

            dados_tabela.append({
                "Nome do Aluno": dados_aluno.get("nome", "Desconhecido"),
                "E-mail institucional": dados_aluno.get("email", "-"),
                "Nota Final": f"{float(item['nota']):.1f}",
                "XP Adquirido": f"+{float(item['pontuacao']):.2f} pts",
                "Data de Conclusão": data_formatada
            })

        st.table(dados_tabela)

    # ============================================================================
    # 👥 VISÃO DO ALUNO: INDICADORES INDIVIDUAIS DE DESEMPENHO
    # ============================================================================
    else:
        cabecalho("Meu Desempenho Acadêmico", "Acompanhe sua evolução e estatísticas gerais de mini-provas")

        try:
            res = supabase.table("historico_provas")\
                .select("nota, pontuacao, data_realizacao")\
                .eq("usuario_id", usuario_id)\
                .execute()
            logs = res.data or []
        except Exception as e:
            st.error(f"Erro ao conectar com a base de dados de performance: {e}")
            logs = []

        if not logs:
            st.warning(f"👋 Olá, {nome_usuario}! Você ainda não realizou nenhuma mini-prova neste semestre.")
            st.info("💡 Assim que você concluir sua primeira avaliação ativa, seus gráficos de evolução, médias acadêmicas e histórico de XP acumulado aparecerão consolidados neste painel.")
            
            st.divider()
            if st.button("⬅️ Voltar para o Painel de Provas", use_container_width=True):
                st.session_state.pagina = "mini_provas"
                st.rerun()
            return

        total_provas = len(logs)
        notas = [float(item["nota"]) for item in logs]
        total_xp = sum([float(item["pontuacao"]) for item in logs])
        
        media_geral = sum(notas) / total_provas if total_provas > 0 else 0.0
        maior_nota = max(notas) if notas else 0.0

        st.markdown(f"### 🎯 Resumo de Conquistas de {nome_usuario}")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("📝 Provas Feitas", f"{total_provas}")
        col2.metric("📊 Média Geral", f"{media_geral:.1f}")
        col3.metric("🔥 Maior Nota", f"{maior_nota:.1f}")
        col4.metric("⭐ Total XP", f"+{total_xp:.2f} pts")

        st.divider()

        st.markdown("### 📈 Curva de Evolução Temporal")
        st.caption("Acompanhe a oscilação das suas notas ao longo das tentativas realizadas.")
        
        historico_grafico = list(reversed(notas))
        st.line_chart(historico_grafico)

        st.divider()

        if media_geral >= 7.0:
            st.success("🚀 Excelente rendimento! Suas métricas indicam ótimo domínio dos tópicos avaliados. Continue mantendo o foco nos próximos simulados!")
        elif media_geral >= 5.0:
            st.info("📈 Bom progresso! Você está na média de aprovação, mas revisando os gabaritos detalhados no histórico poderá alcançar notas ainda maiores.")
        else:
            st.warning("⚠️ Atenção necessária! Suas notas atuais estão abaixo da linha de corte recomendada. Utilize o painel de histórico para revisar os enunciados errados.")

    # Botão de retorno global
    st.divider()
    if st.button("⬅️ Voltar para as Mini Provas", use_container_width=True, type="secondary"):
        st.session_state.pagina = "mini_provas"
        st.rerun()