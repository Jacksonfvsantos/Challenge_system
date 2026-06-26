import streamlit as st
import re
import io
import datetime
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

# Bibliotecas para extração de texto com fallback seguro
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


def extrair_texto_arquivo(arquivo_subido, extensao):
    """Extrai o texto bruto do PDF ou Word submetido."""
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


def parsing_questoes_regex(texto):
    """
    Algoritmo adaptado para capturar exames densos com os padrões 'Exercício X' ou 'Questão X'.
    Mapeia automaticamente o gabarito baseado na linha 'Resposta correta: X'.
    """
    padrao_questao = r'(?:Exercício|Questão|\n)\s*(\d+)[\s\.\-\)]*'
    
    matches = list(re.finditer(padrao_questao, texto, re.IGNORECASE))
    questoes_mapeadas = []

    for i, match in enumerate(matches):
        inicio_bloco = match.start()
        fim_bloco = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        
        bloco_completo = texto[inicio_bloco:fim_bloco].strip()
        if not bloco_completo:
            continue

        linhas = bloco_completo.split('\n')
        enunciado_linhas = []
        alternativas = {}
        gabarito_detectado = "A"

        for linha in linhas:
            linha_str = linha.strip()
            if not linha_str:
                continue

            match_gab = re.search(r'(?:Resposta\s+correta|Gabarito|Resposta):\s*([A-Ea-e])', str(linha_str), re.IGNORECASE)
            if match_gab:
                gabarito_detectado = match_gab.group(1).upper()
                continue

            match_alt = re.match(r'^([A-Ea-e])[\s\.\-\)]+(.*)', linha_str)
            if match_alt:
                letra = match_alt.group(1).upper()
                conteudo_alt = match_alt.group(2).strip()
                alternativas[letra] = conteudo_alt
            else:
                if not alternativas and not linha_str.lower().startswith("exercício") and not linha_str.lower().startswith("questão"):
                    enunciado_linhas.append(linha_str)

        enunciado_completo = " ".join(enunciado_linhas).strip()
        enunciado_completo = re.sub(r'^\d+[\s\.\-\)]*', '', enunciado_completo).strip()

        if enunciado_completo and len(alternativas) >= 2:
            questoes_mapeadas.append({
                "enunciado": enunciado_completo,
                "alternativas": alternativas,
                "gabarito": gabarito_detectado
            })

    return questoes_mapeadas


def tela_mini_provas_professor():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    
    cabecalho("Painel do Docente: Gestão de Mini Provas", "Cadastre novos exames e gerencie avaliações")

    if not usuario_id:
        st.error("Sessão de usuário inválida ou expirada.")
        return

    # 📋 ABAS DISPONÍVEIS
    aba_escopo, aba_manual, aba_importacao = st.tabs([
        "📝 1. Configurar Escopo da Prova", 
        "✍️ 2. Criar Questões do Zero (Manual)", 
        "📂 3. Importar Caderno via PDF/Word"
    ])

    # 📑 ABA 1: METADADOS DA PROVA
    with aba_escopo:
        st.subheader("Configurações Básicas")
        with st.form("form_cadastro_mini_prova", clear_on_submit=True):
            titulo = st.text_input("Título da Mini Prova:", placeholder="Ex: Simulado Prático - Estrutura de Dados")
            descricao = st.text_area("Descrição / Instruções para o Aluno:", placeholder="Descreva as orientações desta avaliação...")
            
            st.markdown("**⏱️ Configurações de Tempo e Prazos:**")
            duracao = st.number_input("Tempo para o aluno responder após iniciar (Minutos):", min_value=1, max_value=180, value=30, step=5)
            
            # ⏳ CAMPOS PEDIDOS: O professor escolhe a data e hora exata limite de expiração
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
                        # Une os inputs de data e hora em um objeto datetime completo fuso-horário ciente
                        expiracao_dt = datetime.datetime.combine(data_limite, hora_limite)
                        
                        payload_prova = {
                            "titulo": titulo.strip(),
                            "descricao": descricao.strip() if descricao else None,
                            "quantidade_questoes": 0,
                            "duracao_minutos": int(duracao),
                            "status": status_prova,
                            "criado_por": usuario_id,
                            "data_expiracao": expiracao_dt.isoformat()  # Salva a timestamp ISO na coluna timestamptz
                        }
                        res = supabase.table("mini_provas").insert(payload_prova).execute()
                        if res.data:
                            st.success(f"✅ Mini Prova '{titulo}' registrada! Ficará ativa até {expiracao_dt.strftime('%d/%m/%Y às %H:%M')}.")
                    except Exception as e:
                        st.error(f"Erro ao salvar mini prova no banco: {e}")

    # Carrega as provas do professor para vinculação nas abas seguintes
    try:
        res_provas = supabase.table("mini_provas").select("id, titulo").eq("criado_por", usuario_id).execute()
        lista_provas = res_provas.data or []
    except Exception:
        lista_provas = []

    if not lista_provas:
        st.info("⚠️ Crie a definição de uma Mini Prova na Aba 1 antes de gerenciar questões.")
        return

    dict_provas = {p["titulo"]: p["id"] for p in lista_provas}

    # 📑 ABA 2: CADASTRO MANUAL DO ZERO
    with aba_manual:
        st.subheader("Cadastro Manual de Questões")
        prova_selecionada_m = st.selectbox("Vincular à qual Mini Prova?", list(dict_provas.keys()), key="sb_manual_p")
        prova_id_m = dict_provas[prova_selecionada_m]

        with st.form("form_questao_manual", clear_on_submit=True):
            enunciado_m = st.text_area("Enunciado da Questão:")
            
            st.markdown("**Alternativas de Múltipla Escolha:**")
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
                        
                        # Atualiza dinamicamente o número de questões na tabela mini_provas
                        prova_atual = supabase.table("mini_provas").select("quantidade_questoes").eq("id", prova_id_m).execute()
                        nova_qtd = (prova_atual.data[0]["quantidade_questoes"] or 0) + 1
                        supabase.table("mini_provas").update({"quantidade_questoes": nova_qtd}).eq("id", prova_id_m).execute()
                        st.success("✅ Questão individual criada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar questão: {e}")

    # 📑 ABA 3: IMPORTAÇÃO INTELIGENTE VIA FILE
    with aba_importacao:
        st.subheader("Upload e Mapeamento Automatizado")
        prova_selecionada_i = st.selectbox("Vincular à qual Mini Prova?", list(dict_provas.keys()), key="sb_import_p")
        prova_id_i = dict_provas[prova_selecionada_i]
        
        arquivo_anexo = st.file_uploader("Suba o arquivo das questões (PDF ou .docx):", type=["pdf", "docx"])
        
        if arquivo_anexo is not None:
            extensao = arquivo_anexo.name.split(".")[-1].lower()
            texto_extraido = extrair_texto_arquivo(arquivo_anexo, extensao)
            
            if texto_extraido:
                questoes_processadas = parsing_questoes_regex(texto_extraido)
                
                if questoes_processadas:
                    st.success(f"🎯 Excelente! O sistema identificou com sucesso {len(questoes_processadas)} questões com gabaritos mapeados!")
                    st.session_state.pool_questoes_importadas = questoes_processadas
                    
                    for idx, q_map in enumerate(questoes_processadas):
                        with st.expander(f"📋 Exercício {idx + 1} — Gabarito Detectado: [{q_map['gabarito']}]", expanded=False):
                            st.write(f"**Enunciado:** {q_map['enunciado']}")
                            for letra, texto_alt in q_map["alternativas"].items():
                                marca = "🟢 (Gabarito Oficial)" if letra == q_map["gabarito"] else ""
                                st.write(f"*{letra})* {texto_alt} {marca}")
                    
                    st.divider()
                    
                    if st.button("💾 CONFIRMAR E SALVAR TODAS AS QUESTÕES NO BANCO DE DADOS", type="primary", use_container_width=True):
                        with st.spinner("Gravando questões relacionais no banco de dados..."):
                            try:
                                successes = 0
                                for q_pool in st.session_state.pool_questoes_importadas:
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
                                
                                # Atualiza o número total real de questões inseridas pelo lote do arquivo
                                prova_atual = supabase.table("mini_provas").select("quantidade_questoes").eq("id", prova_id_i).execute()
                                qtd_antiga = prova_atual.data[0]["quantidade_questoes"] or 0
                                supabase.table("mini_provas").update({"quantidade_questoes": qtd_antiga + successes}).eq("id", prova_id_i).execute()
                                    
                                st.success(f"🔥 Pronto! {successes} questões foram processadas e salvas com seus respectivos gabaritos!")
                                st.session_state.pop("pool_questoes_importadas", None)
                            except Exception as e:
                                st.error(f"Erro na inserção em massa no Supabase: {e}")
                else:
                    st.warning("⚠️ O texto foi extraído, mas nenhum padrão de Exercício/Questão foi reconhecido.")
                    with st.expander("Ver texto bruto extraído", expanded=True):
                        st.text(texto_extraido)

    st.divider()
    if st.button("⬅️ Voltar ao Painel Geral", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()