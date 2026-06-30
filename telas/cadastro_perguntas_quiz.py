import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import (
    aplicar_estilo, 
    cabecalho, 
    formatar_titulo_aba, 
    formatar_legenda_instrucao
)
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia
from services.cadastro_quiz_service import cadastrar_pergunta_completa

def puxar_perguntas_cadastradas(quiz_id):
    try:
        res = supabase.table("perguntas_quiz").select("*").eq("quiz_id", quiz_id).order("ordem").execute()
        return res.data or []
    except Exception:
        return []

def tela_cadastro_perguntas_quiz():
    aplicar_estilo()
    
    if st.button("⬅️ Voltar"): 
        st.session_state.pagina = "quiz_ao_vivo"
        st.rerun()
    
    cabecalho("Caderno de Questões", "Gerenciamento de perguntas síncronas")
    
    formatar_titulo_aba("Nova Pergunta")
    formatar_legenda_instrucao("Adicione perguntas manualmente ou utilize o importador inteligente.")

    try:
        res_quizzes = supabase.table("quizzes").select("id, titulo").order("data_criacao", desc=True).execute()
        lista_quizzes = res_quizzes.data or []
    except Exception as e:
        st.error(f"Erro ao carregar quizzes: {e}")
        return

    if not lista_quizzes:
        st.info("💡 Você precisa criar uma Sala de Quiz primeiro.")
        return

    opcoes_quiz = {q["titulo"]: q["id"] for q in lista_quizzes}
    quiz_selecionado_titulo = st.selectbox("Selecione o Quiz:", list(opcoes_quiz.keys()), key="select_quiz_gerenciar")
    quiz_id = opcoes_quiz[quiz_selecionado_titulo]

    perguntas_atuais = puxar_perguntas_cadastradas(quiz_id)
    st.caption(f"📊 Perguntas cadastradas: **{len(perguntas_atuais)}**")
    st.divider()

    aba_manual, aba_ia = st.tabs(["✍️ Cadastro Manual", "🤖 Importador IA"])

    with aba_manual:
        with st.form("form_nova_pergunta_manual", clear_on_submit=True):
            enunciado = st.text_area("Enunciado da Pergunta")
            tempo_limite = st.slider("Tempo (segundos)", 10, 120, 30, 5)
            
            st.markdown("##### Alternativas")
            alt_a = st.text_input("A")
            alt_b = st.text_input("B")
            alt_c = st.text_input("C")
            alt_d = st.text_input("D")
            
            mapeamento = {"A": 0, "B": 1, "C": 2, "D": 3}
            correta_letra = st.radio("Alternativa CORRETA", list(mapeamento.keys()), horizontal=True)
            
            if st.form_submit_button("💾 Salvar Pergunta", use_container_width=True):
                if not enunciado.strip() or not all([alt_a, alt_b, alt_c, alt_d]):
                    st.error("Preencha todos os campos.")
                else:
                    res = cadastrar_pergunta_completa(quiz_id, enunciado, tempo_limite, [alt_a, alt_b, alt_c, alt_d], mapeamento[correta_letra])
                    if res["sucesso"]:
                        st.success("Salvo com sucesso!")
                        st.rerun()
                    else:
                        st.error(res["mensagem"])

    with aba_ia:
        arquivo = st.file_uploader("Arquivo de referência:", type=["pdf", "docx"])
        prompt = st.text_input("Instruções extras (opcional):")
        
        if arquivo and st.button("Processar com IA", type="primary", use_container_width=True):
            with st.spinner("Analisando documento..."):
                texto = extrair_texto_de_arquivo(arquivo.getvalue(), arquivo.name.split('.')[-1].lower())
                questoes = gerar_questoes_ia(texto, prompt, st.secrets.get("GEMINI_API_KEY"))
                
                if questoes:
                    for q in questoes:
                        cadastrar_pergunta_completa(quiz_id, q["enunciado"], 30, q["alternativas"], q["correta_idx"])
                    st.success("Questões injetadas!")
                    st.rerun()
                else:
                    st.warning("Falha na extração. Verifique o arquivo.")

    if perguntas_atuais:
        with st.expander("👁️ Visualizar Perguntas Salvas"):
            for p in perguntas_atuais:
                st.markdown(f"**Q{p['ordem']}. {p['enunciado']}**")