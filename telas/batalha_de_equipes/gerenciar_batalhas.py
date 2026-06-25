import streamlit as st
import datetime
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import (
    cadastrar_nova_batalha, 
    cadastrar_questao_rapida,
    encerrar_partida_sincrona,
    deletar_batalha,
    obter_batalhas_finalizadas
)

def tela_batalha_gerenciar():
    aplicar_estilo()
    
    cabecalho(
        "🛠️ Painel de Governança Híbrida",
        "Gerencie confrontos ativos, provisione novas batalhas ou consulte o histórico de rodadas passadas"
    )

    # Abas organizadoras de fluxo docente
    aba_ativas, aba_finalizadas = st.tabs(["⚔️ Batalhas Ativas / Agendadas", "📜 Histórico de Confrontos Encerrados"])

    # ------------------------------------------------------------------------
    # ABA 1: CONFRONTOS ATIVOS & AGENDADOS
    # ------------------------------------------------------------------------
    with aba_ativas:
        
        # Gaveta expansível para cadastro rápido de questões se necessário
        with st.expander("➕ Não tem questões prontas? Cadastrar Nova Questão no Banco agora mesmo", expanded=False):
            st.markdown("#### 📝 Nova Questão de Engenharia")
            enunciado_rapido = st.text_area("Enunciado da Questão / Código-fonte do Desafio:", placeholder="Ex: Dado o ponteiro int *p, qual sintaxe extrai o endereço da memória?")
            
            st.markdown("**Opções de Alternativas (Preencha as 4 opções):**")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                alt_a = st.text_input("Alternativa A:", placeholder="Texto da primeira opção", key="qa")
                alt_b = st.text_input("Alternativa B:", placeholder="Texto da segunda opção", key="qb")
            with col_a2:
                alt_c = st.text_input("Alternativa C:", placeholder="Texto da terceira opção", key="qc")
                alt_d = st.text_input("Alternativa D:", placeholder="Texto da quarta opção", key="qd")
                
            opcao_correta = st.selectbox(
                "Qual destas alternativas é a VERDADEIRA?",
                options=[0, 1, 2, 3],
                format_func=lambda x: ["Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D"][x]
            )
            
            if st.button("💾 Gravar Questão no Banco", use_container_width=True):
                if not enunciado_rapido.strip() or not alt_a.strip() or not alt_b.strip() or not alt_c.strip() or not alt_d.strip():
                    st.error("Por favor, preencha o enunciado e todas as 4 alternativas antes de salvar.")
                else:
                    res_q = cadastrar_questao_rapida(
                        enunciado=enunciado_rapido,
                        alternativas_texto=[alt_a, alt_b, alt_c, alt_d],
                        indice_correta=opcao_correta
                    )
                    if res_q["sucesso"]:
                        st.success(res_q["mensagem"])
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(res_q["mensagem"])

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🔥 Painel de Monitoramento Síncrono")

        # Puxa batalhas que NÃO estão finalizadas
        try:
            res_ativas = (
                supabase.table("batalhas")
                .select("*, time_a:time_a_id(nome), time_b:time_b_id(nome)")
                .eq("finalizada", False)
                .order("created_at", descending=True)
                .execute()
            )
            lista_ativas = res_ativas.data or []
        except Exception:
            lista_ativas = []

        if not lista_ativas:
            st.info("Não há nenhuma batalha ativa ou agendada listada no momento.")
        else:
            # ✅ SOLUÇÃO CRÍTICA: Os botões de ação rodam fora de qualquer escopo de formulário
            for bat in lista_ativas:
                t_a = bat.get("time_a", {}).get("nome", "Equipe Desafiante") if bat.get("time_a") else "N/A"
                t_b = bat.get("time_b", {}).get("nome", "Equipe Desafiada") if bat.get("time_b") else "N/A"
                status_str = str(bat.get("status")).upper()

                with st.container(border=True):
                    col_info, col_botoes = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"#### 🏆 {bat['titulo']}")
                        st.markdown(f"**Confronto:** `{t_a}` ⚔️ `{t_b}`")
                        st.markdown(f"**Estado:** `{status_str}` | **Round:** № {bat.get('pergunta_atual_ordem', 1)}")
                    
                    with col_botoes:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("📺 Entrar na Sala", key=f"go_{bat['id']}", use_container_width=True):
                            st.session_state.batalha_ativa_id = bat['id']
                            st.session_state.pagina = "batalha_rodada"
                            st.rerun()
                            
                        if st.button("🛑 Encerrar Desafio", key=f"stop_{bat['id']}", type="secondary", use_container_width=True):
                            if encerrar_partida_sincrona(bat['id']):
                                st.toast("Partida movida para o histórico!", icon="🛑")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Falha ao encerrar a batalha no banco de dados.")
                                
                        if st.button("🗑️ Deletar (Apagar Teste)", key=f"del_{bat['id']}", type="primary", use_container_width=True):
                            if deletar_batalha(bat['id']):
                                st.toast("Registro de teste apagado permanentemente!", icon="🗑️")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Erro ao deletar registro.")

        # Puxa o banco de dados de questões e equipes para alimentar o form abaixo
        try:
            questoes_res = supabase.table("questoes").select("id, enunciado").execute()
            banco_questoes = questoes_res.data or []
            times_res = supabase.table("times").select("id, nome").execute()
            banco_times = times_res.data or []
        except Exception:
            banco_questoes, banco_times = [], []

        st.markdown("<br><hr><br>", unsafe_allow_html=True)
        
        # ✅ CONTAINER ISOLADO: Impede interferência nos botões de cima
        with st.container():
            st.markdown("### 📋 Formular Nova Competição Híbrida")
            
            with st.form("form_abrir_batalha", clear_on_submit=True):
                titulo = st.text_input("Título do Desafio / Batalha:", placeholder="Ex: Batalha de Ponteiros e Alocação Dinâmica")
                descricao = st.text_area("Instruções e Diretrizes Técnicas:", placeholder="Descreva os critérios de avaliação...")
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    modalidade = st.selectbox(
                        "Modalidade da Competição:",
                        options=["sincrona", "assincrona"],
                        format_func=lambda x: "⚡ Síncrona (Ao Vivo / Bate-Rebate)" if x == "sincrona" else "⏳ Assíncrona (Com Prazo Estendido)"
                    )
                with col_m2:
                    if modalidade == "assincrona":
                        data_entrega = st.date_input("Data Limite de Entrega:", datetime.date.today() + datetime.timedelta(days=7))
                        hora_entrega = st.time_input("Horário Limite:", datetime.time(23, 59))
                        prazo_final = datetime.datetime.combine(data_entrega, hora_entrega)
                    else:
                        st.info("💡 Modo Bate-Rebate. O controle de tempo é ditado na sala ao vivo.")
                        prazo_final = None

                time_a_id, time_b_id = None, None
                if modalidade == "sincrona":
                    st.markdown("#### 👥 Seleção de Equipes Competidoras")
                    if len(banco_times) < 2:
                        st.warning("⚠️ São necessárias pelo menos 2 equipes cadastradas para realizar uma disputa.")
                    else:
                        col_t1, col_t2 = st.columns(2)
                        with col_t1:
                            time_a_sel = st.selectbox("Equipe A (Desafiante):", options=banco_times, format_func=lambda x: x["nome"], key="sb_time_a")
                            time_a_id = time_a_sel["id"] if time_a_sel else None
                        with col_t2:
                            banco_times_b = [t for t in banco_times if t["id"] != time_a_id]
                            time_b_sel = st.selectbox("Equipe B (Desafiada):", options=banco_times_b, format_func=lambda x: x["nome"], key="sb_time_b")
                            time_b_id = time_b_sel["id"] if time_b_sel else None

                questoes_selecionadas = []
                if modalidade == "sincrona":
                    st.markdown("#### 🗂️ Seleção de Questões para a Rodada")
                    if not banco_questoes:
                        st.warning("⚠️ Cadastre questões no banco de dados primeiro.")
                    else:
                        # O options recebe a lista de dicionários completa do banco
                        questoes_selecionadas = st.multiselect(
                            "Selecione as questões participantes:",
                            options=banco_questoes,
                            # Exibe o enunciado de forma amigável na interface
                            format_func=lambda x: f"📝 {x.get('enunciado', '')[:80]}..." if len(x.get('enunciado', '')) > 80 else f"📝 {x.get('enunciado', '')}",
                            key="selector_questions_batalha"
                        )

                st.markdown("<br>", unsafe_allow_html=True)
                btn_publicar = st.form_submit_button("🚀 Gravar e Publicar Competição", type="primary", use_container_width=True)

                if btn_publicar:
                    if not titulo.strip():
                        st.error("O título da batalha é obrigatório.")
                    elif modalidade == "sincrona" and (not time_a_id or not time_b_id):
                        st.error("Para o modo Bate-Rebate, selecione duas equipes distintas.")
                    elif modalidade == "sincrona" and not questoes_selecionadas:
                        st.error("Selecione pelo menos 1 questão para compor a rodada.")
                    else:
                        # ✅ CORREÇÃO DEFENSIVA: Extrai o ID usando .get() prevenindo KeyError se a estrutura variar
                        lista_ids = []
                        for q in questoes_selecionadas:
                            if isinstance(q, dict) and "id" in q:
                                lista_ids.append(q["id"])
                            elif isinstance(q, dict) and "_id" in q:
                                lista_ids.append(q["_id"])
                                
                        resultado = cadastrar_nova_batalha(
                            titulo=titulo, 
                            descricao=descricao, 
                            modalidade=modalidade,
                            data_limite=prazo_final, 
                            lista_questoes_ids=lista_ids, # Passa a lista limpa de IDs
                            time_a_id=time_a_id, 
                            time_b_id=time_b_id
                        )
                        
                        if resultado["sucesso"]:
                            st.success(resultado["mensagem"])
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(resultado["mensagem"])

    # ------------------------------------------------------------------------
    # ABA 2: HISTÓRICO DE CONFRONTOS ENCERRADOS
    # ------------------------------------------------------------------------
    with aba_finalizadas:
        st.markdown("### 📜 Arquivo de Confrontos Encerrados")
        
        batalhas_passadas = obter_batalhas_finalizadas()
        
        if not batalhas_passadas:
            st.info("O histórico está limpo. Nenhuma batalha foi arquivada até o momento.")
        else:
            for bat in batalhas_passadas:
                t_a = bat.get("time_a", {}).get("nome", "Equipe Desafiante") if bat.get("time_a") else "N/A"
                t_b = bat.get("time_b", {}).get("nome", "Equipe Desafiada") if bat.get("time_b") else "N/A"
                
                with st.container(border=True):
                    col_hist_info, col_hist_del = st.columns([4, 1])
                    with col_hist_info:
                        st.markdown(f"#### 🏁 {bat['titulo']} (Encerrada)")
                        st.markdown(f"**Disputado entre:** `{t_a}` ⚔️ `{t_b}`")
                        if bat.get("created_at"):
                            st.caption(f"Partida realizada em: {bat['created_at'][:10]}")
                    
                    with col_hist_del:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️ Limpar", key=f"del_hist_{bat['id']}", use_container_width=True):
                            if deletar_batalha(bat['id']):
                                st.toast("Histórico limpo com sucesso!", icon="🗑️")
                                time.sleep(0.5)
                                st.rerun()

    if st.button("⬅️ Sair e Voltar para a Arena", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()