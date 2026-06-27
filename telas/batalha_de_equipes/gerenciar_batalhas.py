import streamlit as st
import datetime
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from utils.importador import extrair_texto_pdf, extrair_texto_docx, parsear_questoes_com_ia
from utils.compartilhamento import exibir_painel_compartilhamento
from services.batalha_service import (
    cadastrar_nova_batalha, cadastrar_questao_rapida,
    encerrar_partida_sincrona, deletar_batalha, obter_batalhas_finalizadas
)

def tela_batalha_gerenciar():
    aplicar_estilo()
    cabecalho("🛠️ Painel de Governança Híbrida", "Gerencie confrontos ativos ou crie novas disputas em tempo real")

    aba_ativas, aba_finalizadas, aba_ia = st.tabs(["⚔️ Batalhas Ativas / Agendadas", "📜 Histórico de Confrontos", "🤖 Importação por IA"])

    with aba_ativas:
        st.markdown("### 🔥 Painel de Monitoramento Síncrono")
        try:
            res_ativas = supabase.table("batalhas").select("*").eq("finalizada", False).order("created_at", descending=True).execute()
            lista_ativas = res_ativas.data or []
        except Exception: 
            lista_ativas = []

        if not lista_ativas:
            st.info("Não há nenhuma batalha ativa listed.")
        else:
            for bat in lista_ativas:
                with st.container(border=True):
                    col_info, col_botoes = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"#### 🏆 {bat['titulo']}")
                        st.markdown(f"**Estado:** `{str(bat.get('status')).upper()}` | Round № {bat.get('pergunta_atual_ordem', 1)}")
                    with col_botoes:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("📺 Entrar na Sala", key=f"go_{bat['id']}", use_container_width=True):
                            st.session_state.batalha_ativa_id = bat['id']
                            st.session_state.pagina = "batalha_rodada"
                            st.rerun()
                        if st.button("🛑 Encerrar Desafio", key=f"stop_{bat['id']}", type="secondary", use_container_width=True):
                            if encerrar_partida_sincrona(bat['id']):
                                st.success("Partida salva no histórico!")
                                time.sleep(0.5)
                                st.rerun()
                    
                    with st.expander("📢 Mapeamento de Links & QR Code para Alunos", expanded=False):
                        exibir_painel_compartilhamento(tipo_sala="batalha", sala_id=bat['id'])

        try:
            banco_questoes = supabase.table("questoes").select("id, enunciado").execute().data or []
            banco_times = supabase.table("times").select("id, nome").execute().data or []
        except Exception: 
            banco_questoes, banco_times = [], []

        st.markdown("<br><hr><br>", unsafe_allow_html=True)
        with st.container():
            st.markdown("### 📋 Formular Nova Competição Híbrida")
            with st.form("form_abrir_batalha", clear_on_submit=True):
                titulo = st.text_input("Título do Desafio:")
                descricao = st.text_area("Instruções:")
                modalidade = st.selectbox("Modalidade:", options=["sincrona", "assincrona"])
                
                time_a_id, time_b_id = None, None
                if modalidade == "sincrona":
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        time_a_sel = st.selectbox("Equipe A:", options=banco_times, format_func=lambda x: x["nome"])
                        time_a_id = time_a_sel["id"] if time_a_sel else None
                    with col_t2:
                        time_b_sel = st.selectbox("Equipe B:", options=banco_times, format_func=lambda x: x["nome"])
                        time_b_id = time_b_sel["id"] if time_b_sel else None

                questoes_selecionadas = st.multiselect("Selecione as questões:", options=banco_questoes, format_func=lambda x: f"📝 {x.get('enunciado', '')[:80]}...")
                
                if st.form_submit_button("🚀 Gravar e Publicar Competição", type="primary", use_container_width=True):
                    if titulo.strip() and questoes_selecionadas:
                        cadastrar_nova_batalha(titulo, descricao, modalidade, None, [q["id"] for q in questoes_selecionadas], time_a_id, time_b_id)
                        st.success("Publicado!")
                        time.sleep(0.5)
                        st.rerun()

    with aba_finalizadas:
        st.markdown("### 📜 Histórico Imutável de Confrontos Encerrados")
        batalhas_passadas = obter_batalhas_finalizadas()
        if not batalhas_passadas:
            st.info("Nenhum histórico permanente localizado.")
        else:
            for bat in batalhas_passadas:
                with st.container(border=True):
                    col_h1, col_h2 = st.columns([4, 1])
                    with col_h1:
                        st.markdown(f"#### 🏁 {bat['titulo']}")
                        st.markdown(f"**Desfecho Oficial:** `{bat.get('resultado_extenso')}`")
                    with col_h2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️ Limpar", key=f"del_h_{bat['id']}", use_container_width=True):
                            supabase.table("historico_batalhas").delete().eq("id", bat['id']).execute()
                            st.success("Removido!")
                            time.sleep(0.5)
                            st.rerun()

    with aba_ia:
        st.markdown("### 🤖 Importador Inteligência Artificial (Gemini 2.5)")
        arq = st.file_uploader("Suba a prova (PDF ou DOCX):", type=["pdf", "docx"])
        if arq and st.button("🔥 Iniciar Extração e Inserção Relacional", type="primary", use_container_width=True):
            with st.spinner("Interpretando com IA..."):
                texto = extrair_texto_pdf(arq) if arq.name.endswith(".pdf") else extrair_texto_docx(arq)
                questoes_geradas = parsear_questoes_com_ia(texto)
                if questoes_geradas:
                    sc = 0
                    for q in questoes_geradas:
                        rq = supabase.table("questoes").insert({"enunciado": q["enunciado"].strip()}).execute()
                        if rq.data:
                            qid = rq.data[0]["id"]
                            alts = [{"questao_id": qid, "texto": a["texto"].strip(), "ordem": i+1, "correta": bool(a["correta"])} for i, a in enumerate(q["alternativas"])]
                            supabase.table("alternativas").insert(alts).execute()
                            sc += 1
                    st.success(f"Sucesso! {sc} questões inseridas no banco.")
                    time.sleep(0.5)
                    st.rerun()

    if st.button("⬅️ Sair e Voltar para a Arena", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()