import streamlit as st
import datetime
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import cadastrar_nova_batalha, cadastrar_questao_rapida

def tela_batalha_gerenciar():
    aplicar_estilo()
    
    cabecalho(
        "🛠️ Painel de Provisionamento Híbrido",
        "Abra novos editais assíncronos ou monte circuitos síncronos de Bate-Rebate entre duas equipes"
    )

    # ------------------------------------------------------------------------
    # GAVETA EXPANSÍVEL: CADASTRO COMPLEMENTAR DIRETO DE QUESTÕES
    # ------------------------------------------------------------------------
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
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res_q["mensagem"])

    st.markdown("<br>", unsafe_allow_html=True)

    # Puxa o banco de dados de questões e equipes do Supabase para os seletores
    try:
        questoes_res = supabase.table("questoes").select("id, enunciado").execute()
        banco_questoes = questoes_res.data or []
    except Exception:
        banco_questoes = []

    try:
        times_res = supabase.table("times").select("id, nome").execute()
        banco_times = times_res.data or []
    except Exception:
        banco_times = []

    # ------------------------------------------------------------------------
    # FORMULÁRIO PRINCIPAL: PROVISIONAMENTO DA COMPETIÇÃO
    # ------------------------------------------------------------------------
    with st.form("form_abrir_batalha", clear_on_submit=False):
        st.markdown("### 📋 Configurações da Partida")
        
        titulo = st.text_input("Título do Desafio / Batalha:", placeholder="Ex: Batalha de Ponteiros e Alocação Dinâmica")
        descricao = st.text_area("Instruções e Diretrizes Técnicas:", placeholder="Descreva os critérios de avaliação ou o escopo do problema...")
        
        col1, col2 = st.columns(2)
        with col1:
            modalidade = st.selectbox(
                "Modalidade da Competição:",
                options=["sincrona", "assincrona"],
                format_func=lambda x: "⚡ Síncrona (Ao Vivo / Bate-Rebate)" if x == "sincrona" else "⏳ Assíncrona (Com Prazo Estendido)"
            )
        
        with col2:
            if modalidade == "assincrona":
                data_entrega = st.date_input("Data Limite de Entrega:", datetime.date.today() + datetime.timedelta(days=7))
                hora_entrega = st.time_input("Horário Limite:", datetime.time(23, 59))
                prazo_final = datetime.datetime.combine(data_entrega, hora_entrega)
            else:
                st.info("💡 Modo Bate-Rebate selecionado. O controle de tempo será ditado em tempo real por si na sala.")
                prazo_final = None

        # ------------------------------------------------------------------------
        # SELEÇÃO SELETIVA DE DUAS EQUIPES COMPETIDORAS (NOVO)
        # ------------------------------------------------------------------------
        time_a_id = None
        time_b_id = None
        
        if modalidade == "sincrona":
            st.markdown("---")
            st.markdown("### 👥 Seleção de Equipes Competidoras")
            st.caption("Escolha as duas equipes específicas que se irão enfrentar ao vivo nesta sala.")
            
            if not banco_times:
                st.warning("⚠️ Nenhuma equipe cadastrada no sistema. Cadastre equipas antes de abrir uma batalha síncrona.")
            elif len(banco_times) < 2:
                st.warning("⚠️ São necessárias pelo menos 2 equipes cadastradas no sistema para realizar um confronto.")
            else:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    time_a_selecionado = st.selectbox(
                        "Selecione a Equipe A (Desafiante):",
                        options=banco_times,
                        format_func=lambda x: x["nome"],
                        key="sb_time_a"
                    )
                    time_a_id = time_a_selecionado["id"] if time_a_selecionado else None
                
                with col_t2:
                    # Filtra a lista da Equipe B para remover o time escolhido na Equipe A
                    banco_times_filtrado_b = [t for t in banco_times if t["id"] != time_a_id]
                    time_b_selecionado = st.selectbox(
                        "Selecione a Equipe B (Desafiada):",
                        options=banco_times_filtrado_b,
                        format_func=lambda x: x["nome"],
                        key="sb_time_b"
                    )
                    time_b_id = time_b_selecionado["id"] if time_b_selecionado else None

        # Exibição das questões disponíveis para o circuito síncrono
        questoes_selecionadas = []
        if modalidade == "sincrona":
            st.markdown("---")
            st.markdown("### 🗂️ Seleção de Questões para o Circuito Síncrono")
            st.caption("Selecione na ordem exata em que deseja que apareçam para os alunos durante o Bate-Rebate.")
            
            if not banco_questoes:
                st.warning("⚠️ Nenhuma questão cadastrada no banco de dados geral. Utilize a gaveta no topo da página para cadastrar questões primeiro.")
            else:
                questoes_selecionadas = st.multiselect(
                    "Selecione as questões participantes:",
                    options=banco_questoes,
                    format_func=lambda x: f"ID: {x['id'][:8]}... | {x['enunciado'][:60]}...",
                    key="selector_questions_batalha"
                )

        st.markdown("<br>", unsafe_allow_html=True)
        btn_publicar = st.form_submit_button("🚀 Gravar e Publicar Competição", type="primary", use_container_width=True)

        if btn_publicar:
            if not titulo.strip():
                st.error("O título da batalha é obrigatório.")
            elif modalidade == "sincrona" and (not time_a_id or not time_b_id):
                st.error("Para o modo Bate-Rebate, deve selecionar duas equipas distintas para competir.")
            elif modalidade == "sincrona" and not questoes_selecionadas:
                st.error("Para o modo Bate-Rebate, selecione pelo menos 1 questão para compor a rodada.")
            else:
                lista_ids = [q["id"] for q in questoes_selecionadas] if modalidade == "sincrona" else []
                
                resultado = cadastrar_nova_batalha(
                    titulo=titulo,
                    descricao=descricao,
                    modalidade=modalidade,
                    data_limite=prazo_final,
                    lista_questoes_ids=lista_ids,
                    time_a_id=time_a_id,
                    time_b_id=time_b_id
                )
                
                if resultado["sucesso"]:
                    st.success(resultado["mensagem"])
                    time.sleep(1)
                    st.session_state.pagina = "batalha_de_equipes"
                    st.rerun()
                else:
                    st.error(resultado["mensagem"])

    if st.button("⬅️ Cancelar e Voltar para a Arena", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()