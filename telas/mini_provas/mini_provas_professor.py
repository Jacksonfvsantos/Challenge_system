import streamlit as st
import datetime
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia

def tela_mini_provas_professor():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    cabecalho("Painel do Docente: Gestão de Mini Provas", "Cadastre novos exames e gerencie avaliações")

    if not usuario_id:
        st.error("Sessão de usuário inválida ou expirada.")
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
                payload = {
                    "titulo": titulo.strip(),
                    "quantidade_questoes": 0,
                    "duracao_minutos": int(duracao),
                    "criado_por": usuario_id,
                    "data_expiracao": data_limite.isoformat()
                }
                if supabase.table("mini_provas").insert(payload).execute().data:
                    st.success("Mini Prova registrada!")
                    st.rerun()

    res_provas = supabase.table("mini_provas").select("id, titulo").eq("criado_por", usuario_id).execute()
    lista_provas = res_provas.data or []
    if not lista_provas:
        st.info("Crie uma Mini Prova na Aba 1.")
        return

    dict_provas = {p["titulo"]: p["id"] for p in lista_provas}
    prova_id = dict_provas[st.selectbox("Vincular à Mini Prova:", list(dict_provas.keys()))]

    with aba_manual:
        with st.form("form_manual", clear_on_submit=True):
            enunciado = st.text_area("Enunciado:")
            alt_a = st.text_input("A:")
            alt_b = st.text_input("B:")
            alt_c = st.text_input("C:")
            alt_d = st.text_input("D:")
            correta = st.selectbox("Correta:", ["A", "B", "C", "D"])
            
            if st.form_submit_button("📥 Gravar"):
                res_q = supabase.table("questoes").insert({"mini_prova_id": prova_id, "enunciado": enunciado}).execute()
                q_id = res_q.data[0]["id"]
                lote = [
                    {"questao_id": q_id, "texto": alt_a, "correta": (correta == "A")},
                    {"questao_id": q_id, "texto": alt_b, "correta": (correta == "B")},
                    {"questao_id": q_id, "texto": alt_c, "correta": (correta == "C")},
                    {"questao_id": q_id, "texto": alt_d, "correta": (correta == "D")}
                ]
                supabase.table("alternativas").insert(lote).execute()
                st.success("Salvo!")

    with aba_importacao:
        arquivo = st.file_uploader("Upload de Caderno (PDF/DOCX):", type=["pdf", "docx"])
        prompt = st.text_input("Instruções extras para a IA:")
        
        if arquivo and st.button("🤖 Processar com IA", type="primary"):
            with st.spinner("IA extraindo e formulando..."):
                texto = extrair_texto_de_arquivo(arquivo.getvalue(), arquivo.name.split('.')[-1])
                questoes = gerar_questoes_ia(texto, prompt, st.secrets.get("GEMINI_API_KEY"))
                
                for q in questoes:
                    res_q = supabase.table("questoes").insert({
                        "mini_prova_id": prova_id, 
                        "enunciado": q["enunciado"]
                    }).execute()
                    q_id = res_q.data[0]["id"]
                    
                    lote = [{"questao_id": q_id, "texto": alt, "correta": (i == q["correta_idx"])} 
                            for i, alt in enumerate(q["alternativas"])]
                    supabase.table("alternativas").insert(lote).execute()
                
                st.success(f"Injetadas {len(questoes)} questões!")
                st.rerun()

    if st.button("⬅️ Voltar"):
        st.session_state.pagina = "mini_provas"
        st.rerun()