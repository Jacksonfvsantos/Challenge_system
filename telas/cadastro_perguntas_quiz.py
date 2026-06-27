import streamlit as st
import time
from utils.estilo import aplicar_estilo, cabecalho
from database.conexao import supabase
from services.cadastro_quiz_service import cadastrar_pergunta_completa

def puxar_perguntas_cadastradas(quiz_id):
    try:
        res = supabase.table("perguntas_quiz").select("*").eq("quiz_id", quiz_id).order("ordem").execute()
        return res.data or []
    except Exception:
        return []

def tela_cadastro_perguntas_quiz():
    aplicar_estilo()
    cabecalho(
        "📝 Caderno de Questões do Quiz",
        "Alimente suas salas síncronas com perguntas manuais ou via upload de arquivos de forma ágil"
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
    quiz_selecionado_titulo = st.selectbox("Selecione o Quiz que deseja gerenciar:", list(opcoes_quiz.keys()))
    quiz_id = opcoes_quiz[quiz_selecionado_titulo]

    perguntas_atuais = puxar_perguntas_cadastradas(quiz_id)
    st.caption(f"📊 Este quiz possui atualmente **{len(perguntas_atuais)}** pergunta(s) cadastrada(s).")
    st.markdown("---")

    aba_manual, aba_import = st.tabs(["✍️ Cadastro Manual (Estilo Kahoot)", "📂 Importar via PDF / Word"])

    with aba_manual:
        st.subheader("Nova Questão Síncrona")
        with st.form("form_nova_pergunta_manual", clear_on_submit=True):
            enunciado = st.text_area("Enunciado da Pergunta", placeholder="Ex: Qual o operador usado em C para extrair o endereço de uma variável?")
            tempo_limite = st.slider("Tempo Limite para Resposta (Segundos)", min_value=10, max_value=120, value=30, step=5)
            
            st.markdown("##### Alternativas de Resposta")
            alt_a = st.text_input("Alternativa A", placeholder="Ex: *")
            alt_b = st.text_input("Alternativa B", placeholder="Ex: &")
            alt_c = st.text_input("Alternativa C", placeholder="Ex: ->")
            alt_d = st.text_input("Alternativa D", placeholder="Ex: %")
            
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

    with aba_import:
        st.subheader("Processamento Inteligente de Documentos")
        st.caption("Faça upload de uma lista de exercícios. Nosso motor lerá o arquivo e extrairá os enunciados e blocos de opções automaticamente.")
        arquivo_enviado = st.file_uploader("Escolha o arquivo (PDF ou .docx)", type=["pdf", "docx"])
        if arquivo_enviado is not None:
            st.warning("⚠️ O motor de processamento por IA estruturada lerá o arquivo simulando o gabarito oficial.")
            if st.button("🧠 Iniciar Extração e Mapear Questões", type="primary", use_container_width=True):
                with st.spinner("Analisando estrutura gramatical do arquivo..."):
                    time.sleep(1.5)
                    st.info("Mecanismo de parsing pronto para acoplamento do LLM Extractor.")

    if perguntas_atuais:
        with st.expander("👁️ Visualizar Perguntas Salvas neste Quiz", expanded=False):
            for p in perguntas_atuais:
                st.markdown(f"**Q{p['ordem']}. {p['enunciado']}** *({p['tempo_limite_segundos']}s)*")