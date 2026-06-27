import streamlit as st
import datetime
import io
import json
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

def extrair_texto_arquivo(arquivo_subido, extensao):
    texto_bruto = ""
    try:
        if extensao == "pdf":
            if PdfReader is None:
                st.error("❌ Erro: O pacote 'pypdf' não está instalado.")
                return ""
            leitor = PdfReader(io.BytesIO(arquivo_subido.read()))
            for pagina in leitor.pages:
                texto_bruto += pagina.extract_text() + "\n"
        elif extensao == "docx":
            if Document is None:
                st.error("❌ Erro: O pacote 'python-docx' não está instalado.")
                return ""
            doc = Document(io.BytesIO(arquivo_subido.read()))
            for paragrafo in doc.paragraphs:
                texto_bruto += paragrafo.text + "\n"
    except Exception as e:
        st.error(f"Erro ao processar a leitura do arquivo: {e}")
    return texto_bruto

def extrair_questoes_com_gemini(texto_prova):
    if genai is None:
        st.error("❌ SDK 'google-genai' não está instalado.")
        return []
        
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("🛑 Chave 'GEMINI_API_KEY' não configurada nos Secrets do Streamlit.")
        return []

    try:
        client = genai.Client(api_key=api_key)
        
        prompt_sistema = (
            "Você é um assistente de engenharia de software acadêmica. Analise o texto de uma prova "
            "e extraia todas as questões de múltipla escolha. Identifique o enunciado de forma limpa, "
            "mapeie as alternativas de A até E (se houver menos, mapeie as existentes) e determine qual é a "
            "alternativa correta (gabarito) com base no texto ou na resolução lógica do problema."
        )

        esquema_saida = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "questoes": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "enunciado": types.Schema(type=types.Type.STRING),
                            "gabarito": types.Schema(type=types.Type.STRING, enum=["A", "B", "C", "D", "E"]),
                            "alternativas": types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "A": types.Schema(type=types.Type.STRING),
                                    "B": types.Schema(type=types.Type.STRING),
                                    "C": types.Schema(type=types.Type.STRING),
                                    "D": types.Schema(type=types.Type.STRING),
                                    "E": types.Schema(type=types.Type.STRING),
                                }
                            )
                        },
                        required=["enunciado", "gabarito", "alternativas"]
                    )
                )
            },
            required=["questoes"]
        )

        config = types.GenerateContentConfig(
            system_instruction=prompt_sistema,
            response_mime_type="application/json",
            response_schema=esquema_saida,
            temperature=0.2
        )

        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=texto_prova,
            config=config
        )
        
        dados_json = json.loads(resposta.text)
        return dados_json.get("questoes", [])
    except Exception as e:
        st.error(f"Falha na inferência da IA (Gemini): {e}")
        return []

def tela_mini_provas_professor():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    cabecalho("Painel do Docente: Gestão de Mini Provas", "Cadastre novos exames e gerencie avaliações")

    if not usuario_id:
        st.error("Sessão de usuário inválida ou expirada.")
        return

    aba_escopo, aba_manual, aba_importacao = st.tabs([
        "📝 1. Configurar Escopo da Prova", 
        "✍️ 2. Criar Questões do Zero (Manual)", 
        "🤖 3. Importar Caderno via IA (Gemini)"
    ])

    with aba_escopo:
        st.subheader("Configurações Básicas")
        with st.form("form_cadastro_mini_prova", clear_on_submit=True):
            titulo = st.text_input("Título da Mini Prova:", placeholder="Ex: Simulado Prático - Estrutura de Dados")
            descricao = st.text_area("Descrição / Instruções para o Aluno:", placeholder="Descreva as orientações desta avaliação...")
            duracao = st.number_input("Tempo para o aluno responder após iniciar (Minutos):", min_value=1, max_value=180, value=30, step=5)
            
            col_data, col_hora = st.columns(2)
            with col_data:
                data_limite = st.date_input("Disponível até o dia:", datetime.date.today())
            with col_hora:
                hora_limite = st.time_input("Disponível até o horário:", datetime.time(23, 59))
            
            status_prova = st.selectbox("Status de Disponibilidade Inicial:", ["Disponível", "Indisponível"])
            btn_salvar_prova = st.form_submit_button("🚀 Criar Definição da Prova", use_container_width=True)
            
            if btn_salvar_prova:
                if not titulo:
                    st.error("Por favor, informe o título da mini prova.")
                else:
                    try:
                        expiracao_dt = datetime.datetime.combine(data_limite, hora_limite)
                        payload_prova = {
                            "titulo": titulo.strip(),
                            "descricao": descricao.strip() if descricao else None,
                            "quantidade_questoes": 0,
                            "duracao_minutos": int(duracao),
                            "status": status_prova,
                            "criado_por": usuario_id,
                            "data_expiracao": expiracao_dt.isoformat()
                        }
                        res = supabase.table("mini_provas").insert(payload_prova).execute()
                        if res.data:
                            st.success(f"✅ Mini Prova '{titulo}' registrada!")
                    except Exception as e:
                        st.error(f"Erro ao salvar mini prova no banco: {e}")

    try:
        res_provas = supabase.table("mini_provas").select("id, titulo").eq("criado_por", usuario_id).execute()
        lista_provas = res_provas.data or []
    except Exception:
        lista_provas = []

    if not lista_provas:
        st.info("⚠️ Crie a definição de uma Mini Prova na Aba 1 antes de gerenciar questões.")
        return

    dict_provas = {p["titulo"]: p["id"] for p in lista_provas}

    with aba_manual:
        st.subheader("Cadastro Manual de Questões")
        prova_selecionada_m = st.selectbox("Vincular à qual Mini Prova?", list(dict_provas.keys()), key="sb_manual_p")
        prova_id_m = dict_provas[prova_selecionada_m]

        with st.form("form_questao_manual", clear_on_submit=True):
            enunciado_m = st.text_area("Enunciado da Questão:")
            alt_a = st.text_input("Alternativa A:")
            alt_b = st.text_input("Alternativa B:")
            alt_c = st.text_input("Alternativa C:")
            alt_d = st.text_input("Alternativa D:")
            alt_e = st.text_input("Alternativa E:")
            gabarito_m = st.selectbox("Qual é a alternativa CORRETA?", ["A", "B", "C", "D", "E"])
            
            btn_salvar_manual = st.form_submit_button("📥 Gravar Questão no Banco", use_container_width=True)
            if btn_salvar_manual:
                if not enunciado_m or not alt_a or not alt_b:
                    st.error("O enunciado e pelo menos as alternativas A e B são obrigatórias.")
                else:
                    try:
                        res_q = supabase.table("questoes").insert({"mini_prova_id": prova_id_m, "enunciado": enunciado_m.strip()}).execute()
                        q_id = res_q.data[0]["id"]
                        
                        lote = []
                        opcoes_map = {"A": alt_a, "B": alt_b, "C": alt_c, "D": alt_d, "E": alt_e}
                        for idx, (letra, texto_alt) in enumerate(opcoes_map.items()):
                            if texto_alt:
                                lote.append({
                                    "questao_id": q_id,
                                    "texto": texto_alt.strip(),
                                    "ordem": idx + 1,
                                    "correta": (letra == gabarito_m)
                                })
                        supabase.table("alternativas").insert(lote).execute()
                        
                        prova_atual = supabase.table("mini_provas").select("quantidade_questoes").eq("id", prova_id_m).execute()
                        nova_qtd = (prova_atual.data[0]["quantidade_questoes"] or 0) + 1
                        supabase.table("mini_provas").update({"quantidade_questoes": nova_qtd}).eq("id", prova_id_m).execute()
                        st.success("✅ Questão individual criada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar questão: {e}")

    with aba_importacao:
        st.subheader("Mapeamento Cognitivo Automatizado por IA")
        prova_selecionada_i = st.selectbox("Vincular à qual Mini Prova?", list(dict_provas.keys()), key="sb_import_p")
        prova_id_i = dict_provas[prova_selecionada_i]
        
        arquivo_anexo = st.file_uploader("Suba o arquivo das questões (PDF ou .docx):", type=["pdf", "docx"])
        if arquivo_anexo is not None:
            extensao = arquivo_anexo.name.split(".")[-1].lower()
            texto_extraido = extrair_texto_arquivo(arquivo_anexo, extensao)
            
            if texto_extraido and st.button("🤖 Processar Caderno com Gemini IA", type="primary", use_container_width=True):
                with st.spinner("O Gemini está interpretando o arquivo e resolvendo as questões..."):
                    questoes_processadas = extrair_questoes_com_gemini(texto_extraido)
                    
                    if questoes_processadas:
                        st.success(f"🎯 Excelente! O Gemini identificou e estruturou {len(questoes_processadas)} questões com gabarito!")
                        st.session_state.pool_questoes_importadas = questoes_processadas
                        st.rerun()
                    else:
                        st.warning("⚠️ Não foi possível estruturar nenhuma questão desse arquivo. Verifique o conteúdo.")

        if "pool_questoes_importadas" in st.session_state:
            questoes_pool = st.session_state.pool_questoes_importadas
            
            for idx, q_map in enumerate(questoes_pool):
                with st.expander(f"📋 Questão Mapeada {idx + 1} — Gabarito Sugerido: [{q_map['gabarito']}]", expanded=False):
                    st.write(f"**Enunciado:** {q_map['enunciado']}")
                    for letra, texto_alt in q_map["alternativas"].items():
                        if texto_alt:
                            marca = "🟢 (Gabarito Oficial)" if letra == q_map["gabarito"] else ""
                            st.write(f"*{letra})* {texto_alt} {marca}")
            
            st.divider()
            if st.button("💾 CONFIRMAR E GRAVAR TODAS AS QUESTÕES NO SUPABASE", type="primary", use_container_width=True):
                with st.spinner("Gravando lote estruturado no banco de dados..."):
                    try:
                        successes = 0
                        for q_pool in questoes_pool:
                            res_q = supabase.table("questoes").insert({"mini_prova_id": prova_id_i, "enunciado": q_pool["enunciado"]}).execute()
                            q_id = res_q.data[0]["id"]
                            
                            lote_alt = []
                            for idx, letra in enumerate(["A", "B", "C", "D", "E"]):
                                texto_alt = q_pool["alternativas"].get(letra, "")
                                if texto_alt:
                                    lote_alt.append({
                                        "questao_id": q_id,
                                        "texto": texto_alt,
                                        "ordem": idx + 1,
                                        "correta": (letra == q_pool["gabarito"])
                                    })
                            if lote_alt:
                                supabase.table("alternativas").insert(lote_alt).execute()
                            successes += 1
                        
                        prova_atual = supabase.table("mini_provas").select("quantidade_questoes").eq("id", prova_id_i).execute()
                        qtd_antiga = prova_atual.data[0]["quantidade_questoes"] or 0
                        supabase.table("mini_provas").update({"quantidade_questoes": qtd_antiga + successes}).eq("id", prova_id_i).execute()
                            
                        st.success(f"🔥 Pronto! {successes} questões foram injetadas com sucesso!")
                        st.session_state.pop("pool_questoes_importadas", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na inserção em massa no Supabase: {e}")

    st.divider()
    if st.button("⬅️ Voltar ao Painel Geral", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()