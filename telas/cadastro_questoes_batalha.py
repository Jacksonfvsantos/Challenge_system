import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho, formatar_titulo_aba
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia
from services.batalha_service import cadastrar_questoes_batalha

def tela_cadastro_questoes_batalha(batalha_id):
    aplicar_estilo()
    cabecalho("Configurar Questões da Batalha")
    
    aba_manual, aba_ia = st.tabs(["✍️ Manual", "🤖 IA"])
    
    with aba_ia:
        arquivo = st.file_uploader("Upload PDF/DOCX", type=["pdf", "docx"], key="ia_batalha")
        prompt = st.text_input("Instruções extras para a IA:")
        
        if arquivo and st.button("Processar com IA", type="primary"):
            with st.spinner("Extraindo e processando questões..."):
                extensao = arquivo.name.split('.')[-1]
                texto = extrair_texto_de_arquivo(arquivo.getvalue(), extensao)
                questoes = gerar_questoes_ia(texto, prompt, st.secrets["GEMINI_API_KEY"])
                
                if questoes:
                    res = cadastrar_questoes_batalha(batalha_id, questoes)
                    if res["sucesso"]:
                        st.success("Questões importadas com sucesso!")
                        st.rerun()
                    else:
                        st.error(res["mensagem"])
                else:
                    st.warning("Nenhuma questão foi gerada pelo arquivo.")

    with aba_manual:
        formatar_titulo_aba("Nova Questão Manual")
        with st.form("form_manual_batalha", clear_on_submit=True):
            enunciado = st.text_area("Enunciado da Pergunta")
            a = st.text_input("Alternativa A")
            b = st.text_input("Alternativa B")
            c = st.text_input("Alternativa C")
            d = st.text_input("Alternativa D")
            correta = st.selectbox("Alternativa Correta", ["A", "B", "C", "D"])
            
            if st.form_submit_button("Salvar Questão"):
                mapeamento = {"A": 0, "B": 1, "C": 2, "D": 3}
                dados_questao = [{
                    "enunciado": enunciado,
                    "alternativas": [a, b, c, d],
                    "correta_idx": mapeamento[correta]
                }]
                
                res = cadastrar_questoes_batalha(batalha_id, dados_questao)
                if res["sucesso"]:
                    st.success("Questão salva!")
                    st.rerun()
                else:
                    st.error(res["mensagem"])