import streamlit as st
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

def tela_desempenho_mini_provas():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
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

        # Cria as opções do Selectbox incluindo a opção de Rendimento Geral
        opcoes_selecao = ["📊 [Geral] Rendimento Consolidado de Todas as Provas"]
        dict_provas = {}
        for p in lista_provas:
            opcoes_selecao.append(p["titulo"])
            dict_provas[p["titulo"]] = p["id"]

        prova_selecionada = st.selectbox("Selecione a Mini-prova para auditar:", opcoes_selecao)

        # 2. Busca e filtra os dados com base na seleção (Global vs Específica)
        try:
            if prova_selecionada == "📊 [Geral] Rendimento Consolidado de Todas as Provas":
                # Busca o histórico completo de todas as provas para calcular o rendimento geral
                res_historico = supabase.table("historico_provas")\
                    .select("nota, pontuacao, data_realizacao, usuarios(nome, email)")\
                    .execute()
                logs_brutos = res_historico.data or []
            else:
                # Busca apenas da prova selecionada
                prova_id_alvo = dict_provas[prova_selecionada]
                res_historico = supabase.table("historico_provas")\
                    .select("nota, pontuacao, data_realizacao, usuarios(nome, email)")\
                    .eq("mini_prova_id", prova_id_alvo)\
                    .execute()
                logs_brutos = res_historico.data or []
        except Exception as e:
            st.error(f"Erro ao buscar dados do banco: {e}")
            logs_brutos = []

        if not logs_brutos:
            st.warning(f"📋 Nenhuma tentativa de resolução foi registrada para a seleção atual.")
            st.divider()
            if st.button("⬅️ Voltar para o Painel Geral", use_container_width=True):
                st.session_state.pagina = "mini_provas"
                st.rerun()
            return

        # 3. Processamento das métricas e agrupamento se for Visão Geral
        dados_tabela = []
        
        if prova_selecionada == "📊 [Geral] Rendimento Consolidado de Todas as Provas":
            # Agrupa por aluno para tirar a média real de todas as participações
            agrupado = {}
            for item in logs_brutos:
                dados_aluno = item.get("usuarios", {}) or {}
                email = dados_aluno.get("email")
                if not email:
                    continue
                if email not in agrupado:
                    agrupado[email] = {
                        "nome": dados_aluno.get("nome", "Desconhecido"),
                        "notas": [],
                        "xp": 0.0,
                        "ultima_data": item.get("data_realizacao")
                    }
                agrupado[email]["notas"].append(float(item["nota"]))
                agrupado[email]["xp"] += float(item["pontuacao"])
                if item.get("data_realizacao", "") > agrupado[email]["ultima_data"]:
                    agrupado[email]["ultima_data"] = item.get("data_realizacao")

            for email, info in agrupado.items():
                media_calculada = sum(info["notas"]) / len(info["notas"])
                dados_tabela.append({
                    "Nome do Aluno": info["nome"],
                    "E-mail institucional": email,
                    "Nota Final": media_calculada,
                    "XP Adquirido": info["xp"],
                    "Data de Conclusão": info["ultima_data"].split("T")[0] if "T" in str(info["ultima_data"]) else str(info["ultima_data"])
                })
                
            total_avaliados = len(dados_tabela)
            todas_medias = [item["Nota Final"] for item in dados_tabela]
            media_geral_painel = sum(todas_medias) / total_avaliados if total_avaliados > 0 else 0.0
            maior_nota_painel = max(todas_medias) if todas_medias else 0.0
            titulo_indicadores = "🎯 Indicadores Consolidados de Todo o Semestre"
        else:
            # Visão de uma prova específica mapeada
            for item in logs_brutos:
                dados_aluno = item.get("usuarios", {}) or {}
                data_iso = item.get("data_realizacao", "")
                data_formatada = data_iso.split("T")[0] if "T" in str(data_iso) else str(data_iso)
                
                dados_tabela.append({
                    "Nome do Aluno": dados_aluno.get("nome", "Desconhecido"),
                    "E-mail institucional": dados_aluno.get("email", "-"),
                    "Nota Final": float(item["nota"]),
                    "XP Adquirido": float(item["pontuacao"]),
                    "Data de Conclusão": data_formatada
                })
            
            total_avaliados = len(dados_tabela)
            todas_notas = [item["Nota Final"] for item in dados_tabela]
            media_geral_painel = sum(todas_notas) / total_avaliados if total_avaliados > 0 else 0.0
            maior_nota_painel = max(todas_notas) if todas_notas else 0.0
            titulo_indicadores = f"🎯 Indicadores Gerais — {prova_selecionada}"

        # Exibe os blocos de métricas superiores
        st.markdown(f"### {titulo_indicadores}")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("👥 Alunos Avaliados", f"{total_avaliados}")
        col_m2.metric("📊 Média da Turma", f"{media_geral_painel:.1f} / 10.0")
        col_m3.metric("🔥 Maior Nota Registrada", f"{maior_nota_painel:.1f}")

        st.divider()

        # 4. 🎛️ PAINEL PEDIDO: FILTROS DE ORDENAÇÃO DINÂMICA DA TABELA
        st.markdown("### 📋 Listagem Nominal de Rendimento")
        
        col_ord1, col_ord2 = st.columns(2)
        with col_ord1:
            coluna_alvo = st.selectbox("Ordenar a tabela por:", ["Nota Final", "Nome do Aluno", "Data de Conclusão"])
        with col_ord2:
            direto_ordem = st.selectbox("Direção da ordenação:", ["Decrescente (Maior para Menor)", "Crescente (Menor para Maior)"])

        # Executa a ordenação com base nas escolhas do professor
        reverso = True if "Decrescente" in direto_ordem else False
        dados_tabela = sorted(dados_tabela, key=lambda x: x[coluna_alvo], reverse=reverso)

        # Formata os dados numéricos antes de renderizar a tabela na tela
        dados_formatados_exibicao = []
        for linha in dados_tabela:
            dados_formatados_exibicao.append({
                "Nome do Aluno": linha["Nome do Aluno"],
                "E-mail institucional": linha["E-mail institucional"],
                "Nota Final": f"{linha['Nota Final']:.1f}",
                "XP Adquirido": f"+{linha['XP Adquirido']:.2f} pts",
                "Data de Conclusão": linha["Data de Conclusão"]
            })

        st.table(dados_formatados_exibicao)

    # ============================================================================
    # 👥 VISÃO DO ALUNO: INDICADORES INDIVIDUAIS DE DESEMPENHO
    # ============================================================================
    else:
        cabecalho("📊 Meu Desempenho Acadêmico", "Acompanhe sua evolução e estatísticas gerais de mini-provas")

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