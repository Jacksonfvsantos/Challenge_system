import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
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
    col_nav, col_vazio = st.columns([1, 5])
    with col_nav:
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
    cabecalho(
        "📝 Caderno de Questões do Quiz",
        "Alimente suas salas síncronas com perguntas manuais ou extraídas via inteligência artificial"
    )

    try:
        res_quizzes = supabase.table("quizzes").select("id, titulo").order("data_criacao", desc=True).execute()
        lista_quizzes = res_quizzes.data or []
    except Exception as e:
        st.error(f"Erro ao carregar seus quizzes: {e}")
        return

    if not lista_quizzes:
        st.info("💡 Você precisa criar uma Sala de Quiz primeiro na tela anterior antes de adicionar perguntas.")
        return

    opcoes_quiz = {q["titulo"]: q["id"] for q in lista_quizzes}
    quiz_selecionado_titulo = st.selectbox("Selecione o Quiz que deseja gerenciar:", list(opcoes_quiz.keys()), key="select_quiz_gerenciar")
    quiz_id = opcoes_quiz[quiz_selecionado_titulo]

    perguntas_atuais = puxar_perguntas_cadastradas(quiz_id)
    st.caption(f"📊 Este quiz possui atualmente **{len(perguntas_atuais)}** pergunta(s) cadastrada(s).")
    st.divider()

    aba_manual, aba_ia = st.tabs(["✍️ Cadastro Manual", "🤖 Importador IA (PDF/DOCX)"])

    with aba_manual:
        st.subheader("Nova Questão Síncrona")
        with st.form("form_nova_pergunta_manual", clear_on_submit=True):
            enunciado = st.text_area("Enunciado da Pergunta", placeholder="Digite o enunciado...")
            tempo_limite = st.slider("Tempo Limite para Resposta (Segundos)", min_value=10, max_value=120, value=30, step=5)
            
            st.markdown("##### Alternativas de Resposta")
            alt_a = st.text_input("Alternativa A")
            alt_b = st.text_input("Alternativa B")
            alt_c = st.text_input("Alternativa C")
            alt_d = st.text_input("Alternativa D")
            
            mapeamento_letras = {"Alternativa A": 0, "Alternativa B": 1, "Alternativa C": 2, "Alternativa D": 3}
            correta_letra = st.radio("Qual é a alternativa CORRETA?", list(mapeamento_letras.keys()), horizontal=True)
            
            btn_salvar = st.form_submit_button("💾 Salvar Pergunta no Caderno", use_container_width=True)
            if btn_salvar:
                if not enunciado.strip() or not all([alt_a.strip(), alt_b.strip(), alt_c.strip(), alt_d.strip()]):
                    st.error("Preencha o enunciado e todas as 4 alternativas antes de salvar.")
                else:
                    lista_alt = [alt_a, alt_b, alt_c, alt_d]
                    idx_correta = mapeamento_letras[correta_letra]
                    
                    with st.spinner("Gravando questão..."):
                        res = cadastrar_pergunta_completa(quiz_id, enunciado, tempo_limite, lista_alt, idx_correta)
                        if res["sucesso"]:
                            st.success(res["mensagem"])
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(res["mensagem"])

    with aba_ia:
        st.subheader("🤖 Importador Automático (PDF/DOCX)")
        arquivo = st.file_uploader("Arquivo de referência:", type=["pdf", "docx"], key="ia_quiz_upload")
        prompt = st.text_input("Instruções de geração (Ex: foque em cálculos):", key="ia_quiz_prompt")
        
        if arquivo and st.button("Processar Documento com IA", type="primary", use_container_width=True, key="btn_ia_quiz_process"):
            with st.spinner("A IA está analisando o documento..."):
                extensao = arquivo.name.split('.')[-1].lower()
                texto = extrair_texto_de_arquivo(arquivo.getvalue(), extensao)
                
                api_key = st.secrets.get("GEMINI_API_KEY")
                questoes = gerar_questoes_ia(texto, prompt, api_key)
                
                if questoes:
                    for q in questoes:
                        cadastrar_pergunta_completa(quiz_id, q["enunciado"], 30, q["alternativas"], q["correta_idx"])
                    st.success(f"⚡ {len(questoes)} questões injetadas com sucesso neste quiz!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("⚠️ Falha na estruturação JSON pela IA. Verifique o arquivo.")

    if perguntas_atuais:
        with st.expander("👁️ Visualizar Perguntas Salvas neste Quiz", expanded=False):
            for p in perguntas_atuais:
                st.markdown(f"**Q{p['ordem']}. {p['enunciado']}** *({p['tempo_limite_segundos']}s)*")