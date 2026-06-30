import streamlit as st
import datetime
from utils.estilo import aplicar_estilo, cabecalho
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia
from services.mini_prova_service import (
    criar_escopo_mini_prova, 
    listar_provas_professor,
    salvar_questao_com_alternativas, 
    salvar_questoes_lote_ia
)

def tela_mini_provas_professor():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    cabecalho("Painel do Docente: Gestão de Mini Provas", "Cadastre novos exames e gerencie avaliações")

    if not usuario_id:
        st.error("Sessão de utilizador inválida ou expirada.")
        return

    aba_escopo, aba_manual, aba_importacao = st.tabs([
        "📝 1. Configurar Escopo", 
        "✍️ 2. Cadastro Manual", 
        "🤖 3. Importação IA"
    ])

    with aba_escopo:
        with st.form("form_cadastro_mini_prova", clear_on_submit=True):
            titulo = st.text_input("Título da Mini Prova:")
            duracao = st.number_input("Duração (Minutos):", min_value=1, value=30)
            data_limite = st.date_input("Disponível até:", datetime.date.today())
            
            if st.form_submit_button("🚀 Criar Definição da Prova"):
                res = criar_escopo_mini_prova(titulo, duracao, usuario_id, data_limite.isoformat())
                if res["sucesso"]:
                    st.success("Mini Prova registada com sucesso!")
                    st.rerun()
                else:
                    st.error(res["mensagem"])

    # Carrega provas usando o serviço em vez do Supabase direto
    lista_provas = listar_provas_professor(usuario_id)
    if not lista_provas:
        st.info("Crie o escopo de uma Mini Prova na Aba 1 para continuar.")
        return

    dict_provas = {p["titulo"]: p["id"] for p in lista_provas}
    prova_id = dict_provas[st.selectbox("Vincular questões à Mini Prova:", list(dict_provas.keys()))]

    with aba_manual:
        with st.form("form_manual", clear_on_submit=True):
            enunciado = st.text_area("Enunciado:")
            alt_a = st.text_input("Alternativa A:")
            alt_b = st.text_input("Alternativa B:")
            alt_c = st.text_input("Alternativa C:")
            alt_d = st.text_input("Alternativa D:")
            correta = st.selectbox("Alternativa Correta:", ["A", "B", "C", "D"])
            
            if st.form_submit_button("📥 Gravar Questão"):
                res = salvar_questao_com_alternativas(prova_id, enunciado, [alt_a, alt_b, alt_c, alt_d], correta)
                if res["sucesso"]:
                    st.success(res["mensagem"])
                else:
                    st.error(f"Erro: {res['mensagem']}")

    with aba_importacao:
        arquivo = st.file_uploader("Upload de Caderno (PDF/DOCX):", type=["pdf", "docx"])
        prompt = st.text_input("Instruções extras para a IA:")
        
        if arquivo and st.button("🤖 Processar e Injetar com IA", type="primary"):
            with st.spinner("A IA está a extrair e formular as questões..."):
                texto = extrair_texto_de_arquivo(arquivo.getvalue(), arquivo.name.split('.')[-1])
                questoes_geradas = gerar_questoes_ia(texto, prompt, st.secrets.get("GEMINI_API_KEY"))
                
                res = salvar_questoes_lote_ia(prova_id, questoes_geradas)
                if res["sucesso"]:
                    st.success(res["mensagem"])
                    st.rerun()
                else:
                    st.error(f"Falha na importação: {res['mensagem']}")

    if st.button("⬅️ Voltar ao Painel", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()