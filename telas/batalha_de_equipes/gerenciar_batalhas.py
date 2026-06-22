import streamlit as st
import datetime
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import cadastrar_nova_batalha

def tela_batalha_gerenciar():
    aplicar_estilo()
    
    cabecalho(
        "🛠️ Painel de Provisionamento Híbrido",
        "Abra novos editais assíncronos ou monte circuitos síncronos de Bate-Rebate"
    )

    # Puxa o banco de questões prontas para o professor selecionar
    try:
        questoes_res = supabase.table("questoes").select("id, enunciado").execute()
        banco_questoes = questoes_res.data or []
    except Exception:
        banco_questoes = []

    with st.form("form_abrir_batalha", clear_on_submit=True):
        st.markdown("### 📝 Configurações da Partida")
        
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
                # Data limite para o modo assíncrono
                data_entrega = st.date_input("Data Limite de Entrega:", datetime.date.today() + datetime.timedelta(days=7))
                hora_entrega = st.time_input("Horário Limite:", datetime.time(23, 59))
                prazo_final = datetime.datetime.combine(data_entrega, hora_entrega)
            else:
                st.info("💡 Modo Bate-Rebate selecionado. O controle de tempo será ditado em tempo real por você na sala.")
                prazo_final = None

        # Se for síncrona, abre a seleção múltipla de questões
        questoes_selecionadas = []
        if modalidade == "sincrona":
            st.markdown("---")
            st.markdown("### 🗂️ Seleção de Questões para o Circuito Síncrono")
            st.caption("Selecione na ordem exata em que deseja que elas apareçam para os alunos durante o Bate-Rebate.")
            
            if not banco_questoes:
                st.warning("⚠️ Nenhuma questão cadastrada no banco de dados geral. Cadastre questões primeiro.")
            else:
                # Criar um multiselect amigável mostrando o início do enunciado
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
            elif modalidade == "sincrona" and not questoes_selecionadas:
                st.error("Para o modo Bate-Rebate, selecione pelo menos 1 questão para compor a rodada.")
            else:
                lista_ids = [q["id"] for q in questoes_selecionadas] if modalidade == "sincrona" else []
                
                resultado = cadastrar_nova_batalha(
                    titulo=titulo,
                    descricao=descricao,
                    modalidade=modalidade,
                    data_limite=prazo_final,
                    lista_questoes_ids=lista_ids
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
