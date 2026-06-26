import streamlit as st
import datetime
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from utils.importador import extrair_texto_pdf, extrair_texto_docx, parsear_questoes_com_ia
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
        "Gerencie confrontos ativos, provisione novas batalhas ou importe avaliações em lote"
    )

    aba_ativas, aba_finalizadas, aba_ia = st.tabs([
        "⚔️ Batalhas Ativas / Agendadas", 
        "📜 Histórico de Confrontos", 
        "🤖 Importação por IA"
    ])

    with aba_ativas:
        with st.expander("➕ Não tem questões prontas? Cadastrar Nova Questão Individual", expanded=False):
            st.markdown("#### 📝 Nova Questão de Engenharia")
            enunciado_rapido = st.text_area("Enunciado da Questão / Código-fonte:")
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                alt_a = st.text_input("Alternativa A:", key="qa")
                alt_b = st.text_input("Alternativa B:", key="qb")
            with col_a2:
                alt_c = st.text_input("Alternativa C:", key="qc")
                alt_d = st.text_input("Alternativa D:", key="qd")
                
            opcao_correta = st.selectbox(
                "Qual destas alternativas é a VERDADEIRA?",
                options=[0, 1, 2, 3],
                format_func=lambda x: ["Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D"][x]
            )
            
            if st.button("💾 Gravar Questão Individual", use_container_width=True):
                if not enunciado_rapido.strip() or not alt_a.strip() or not alt_b.strip() or not alt_c.strip() or not alt_d.strip():
                    st.error("Por favor, preencha todos os campos antes de salvar.")
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

        try:
            res_ativas = (
                supabase.table("batalhas")
                .select("*")
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
            for bat in lista_ativas:
                with st.container(border=True):
                    col_info, col_botoes = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"#### 🏆 {bat['titulo']}")
                        st.markdown(f"**Estado:** `{str(bat.get('status')).upper()}` | **Round:** № {bat.get('pergunta_atual_ordem', 1)}")
                    
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
                                
                        if st.button("🗑️ Deletar (Apagar Teste)", key=f"del_{bat['id']}", type="primary", use_container_width=True):
                            if deletar_batalha(bat['id']):
                                st.toast("Registro apagado permanente!", icon="🗑️")
                                time.sleep(0.5)
                                st.rerun()

        try:
            questoes_res = supabase.table("questoes").select("id, enunciado").execute()
            banco_questoes = questoes_res.data or []
            times_res = supabase.table("times").select("id, nome").execute()
            banco_times = times_res.data or []
        except Exception:
            banco_questoes, banco_times = [], []

        st.markdown("<br><hr><br>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("### 📋 Formular Nova Competição Híbrida")
            with st.form("form_abrir_batalha", clear_on_submit=True):
                titulo = st.text_input("Título do Desafio / Batalha:")
                descricao = st.text_area("Instruções Técnicas:")
                
                modalidade = st.selectbox("Modalidade:", options=["sincrona", "assincrona"])
                prazo_final = None

                time_a_id, time_b_id = None, None
                if modalidade == "sincrona":
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        time_a_sel = st.selectbox("Equipe A:", options=banco_times, format_func=lambda x: x["nome"], key="sb_time_a")
                        time_a_id = time_a_sel["id"] if time_a_sel else None
                    with col_t2:
                        time_b_sel = st.selectbox("Equipe B:", options=banco_times, format_func=lambda x: x["nome"], key="sb_time_b")
                        time_b_id = time_b_sel["id"] if time_b_sel else None

                questoes_selecionadas = st.multiselect(
                    "Selecione as questões participantes:",
                    options=banco_questoes,
                    format_func=lambda x: f"📝 {x.get('enunciado', '')[:80]}..."
                )

                btn_publicar = st.form_submit_button("🚀 Gravar e Publicar Competição", type="primary", use_container_width=True)
                if btn_publicar:
                    if not titulo.strip():
                        st.error("Título obrigatório.")
                    elif modalidade == "sincrona" and time_a_id == time_b_id:
                        st.error("Selecione equipes diferentes.")
                    elif not questoes_selecionadas:
                        st.error("Selecione pelo menos 1 questão.")
                    else:
                        lista_ids = [q["id"] for q in questoes_selecionadas]
                        resultado = cadastrar_nova_batalha(
                            titulo=titulo, descricao=descricao, modalidade=modalidade,
                            data_limite=prazo_final, lista_questoes_ids=lista_ids,
                            time_a_id=time_a_id, time_b_id=time_b_id
                        )
                        if resultado["sucesso"]:
                            st.success(resultado["mensagem"])
                            time.sleep(0.5)
                            st.rerun()

    with aba_finalizadas:
        st.markdown("### 📜 Arquivo de Confrontos Encerrados")
        batalhas_passadas = obter_batalhas_finalizadas()
        if not batalhas_passadas:
            st.info("Nenhuma batalha arquivada.")
        else:
            for bat in batalhas_passadas:
                with st.container(border=True):
                    col_hist_info, col_hist_del = st.columns([4, 1])
                    with col_hist_info:
                        st.markdown(f"#### 🏁 {bat['titulo']} (Encerrada)")
                    with col_hist_del:
                        if st.button("🗑️ Limpar", key=f"del_hist_{bat['id']}", use_container_width=True):
                            if deletar_batalha(bat['id']):
                                st.success("Histórico limpo!")
                                time.sleep(0.5)
                                st.rerun()

    # 🤖 NOVA ABA: PROCESSAMENTO AUTOMÁTICO DE PROVAS COM IA
    with aba_ia:
        st.markdown("### 🤖 Provisionamento Automatizado por Inteligência Artificial")
        st.caption("Faça upload de um arquivo contendo enunciados, opções e gabaritos. A IA irá mapear e salvar a estrutura diretamente no banco.")
        
        arquivo_upload = st.file_uploader("Carregar Avaliação (PDF ou DOCX):", type=["pdf", "docx"], key="ia_file_uploader")
        
        if arquivo_upload:
            if st.button("🔥 Iniciar Mapeamento e Inserção Relacional", type="primary", use_container_width=True):
                with st.spinner("Extraindo textos brutos e consultando o modelo Gemini..."):
                    if arquivo_upload.name.endswith(".pdf"):
                        texto_bruto = extrair_texto_pdf(arquivo_upload)
                    else:
                        texto_bruto = extrair_texto_docx(arquivo_upload)
                        
                    if not texto_bruto.strip():
                        st.error("Não foi possível extrair texto legível deste documento.")
                    else:
                        questoes_geradas = parsear_questoes_com_ia(texto_bruto)
                        
                        if questoes_geradas:
                            sucessos = 0
                            for q in questoes_geradas:
                                res_q = supabase.table("questoes").insert({"enunciado": q["enunciado"].strip()}).execute()
                                if res_q.data:
                                    q_id = res_q.data[0]["id"]
                                    linhas_alt = []
                                    for i, alt in enumerate(q["alternativas"]):
                                        linhas_alt.append({
                                            "questao_id": q_id,
                                            "texto": alt["texto"].strip(),
                                            "ordem": i + 1,
                                            "correta": bool(alt["correta"])
                                        })
                                    supabase.table("alternativas").insert(linhas_alt).execute()
                                    sucessos += 1
                                    
                            st.success(f"🎯 Extração concluída! {sucessos} questões estruturadas salvas com sucesso!")
                            time.sleep(1.0)
                            st.rerun()

    if st.button("⬅️ Sair e Voltar para a Arena", use_container_width=True, key="btn_exit_gov_hybrid"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()