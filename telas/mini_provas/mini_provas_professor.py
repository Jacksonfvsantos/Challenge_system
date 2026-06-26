import streamlit as st
import re
import io
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
    Algoritmo de parsing robusto focado em capturar exames densos (+30 questões).
    Identifica padrões flexíveis de numeração e busca o gabarito no próprio texto.
    """
    # Expressão regular flexível: detecta números de 1 a 99 seguidos de ponto, traço ou parêntese
    padrao_questao = r'(?:Questão\s+)?(\d+)[\s\.\-\)]+'
    
    # Encontra todas as posições onde começam as questões no documento
    matches = list(re.finditer(padrao_questao, texto, re.IGNORECASE))
    questoes_mapeadas = []

    for i, match in enumerate(matches):
        inicio_bloco = match.start()
        fim_bloco = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        
        bloco_completo = texto[inicio_bloco:fim_bloco].strip()
        if not bloco_completo:
            continue

        # Quebra o bloco em linhas para separar enunciado de alternativas
        linhas = bloco_completo.split('\n')
        enunciado_linhas = []
        alternativas = {}
        gabarito_detectado = "A"  # Fallback padrão seguro

        # ✅ CORRIGIDO: alterado de 'lines' para 'linhas' para casar com a variável acima
        for linha in linhas:
            linha_str = linha.strip()
            if not linha_str:
                continue

            # Identifica alternativas como: A) texto, B - texto, *C) correto, D. texto
            match_alt = re.search(r'(?:\*|\[X\]|\(X\))?\s*([A-Ea-e])[\s\.\-\)]+(.*)', linha_str)
            
            if match_alt:
                letra = match_alt.group(1).upper()
                conteudo_alt = match_alt.group(2).strip()
                alternativas[letra] = conteudo_alt
                
                # Se a linha continha um marcador de sucesso no documento original, define o gabarito
                if '*' in linha_str or '[X]' in linha_str.upper() or '(X)' in linha_str.upper():
                    gabarito_detectado = letra
            else:
                # Se a linha também contiver um padrão explícito isolado no fim (Ex: "Gabarito: C")
                match_gab_final = re.search(r'(?:Gabarito|Resposta):\s*([A-E])', linha_str, re.IGNORECASE)
                if match_gab_final:
                    gabarito_detectado = match_gab_final.group(1).upper()
                elif not alternativas:
                    enunciado_linhas.append(linha_str)

        enunciado_completo = " ".join(enunciado_linhas).strip()
        # Limpa o numeral da questão do início do enunciado
        enunciado_completo = re.sub(r'^(?:Questão\s+)?\d+[\s\.\-\)]*', '', enunciado_completo).strip()

        # Só adiciona se possuir conteúdo consistente
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

    # 📋 TRÊS ABAS DISPONÍVEIS: Escopo, Cadastro Manual do Zero, Importação Automatizada
    aba_escopo, aba_manual, aba_importacao = st.tabs([
        "📝 1. Configurar Escopo da Prova", 
        "✍️ 2. Criar Questões do Zero (Manual)", 
        "📂 3. Importar Caderno via PDF/Word"
    ])

    # 📑 ABA 1: METADADOS DA PROVA
    with aba_escopo:
        st.subheader("Configurações Básicas")
        with st.form("form_cadastro_mini_prova", clear_on_submit=True):
            titulo = st.text_input("Título da Mini Prova:", placeholder="Ex: Simulado Prático - Camadas OSI")
            descricao = st.text_area("Descrição / Instruções para o Aluno:", placeholder="Descreva as orientações desta avaliação...")
            col1, col2 = st.columns(2)
            qtd_questoes = col1.number_input("Quantidade Total de Questões:", min_value=1, max_value=50, value=5, step=1)
            duracao = col2.number_input("Duração Limite (Minutos):", min_value=1, max_value=180, value=30, step=5)
            status_prova = st.selectbox("Status de Disponibilidade Inicial:", ["Disponível", "Indisponível"])
            
            btn_salvar_prova = st.form_submit_button("🚀 Criar Definição da Prova", use_container_width=True)
            if btn_salvar_prova:
                if not titulo:
                    st.error("Por favor, informe o título da mini prova.")
                else:
                    try:
                        payload_prova = {
                            "titulo": titulo.strip(),
                            "descricao": descricao.strip() if descricao else None,
                            "quantidade_questoes": int(qtd_questoes),
                            "duracao_minutos": int(duracao),
                            "status": status_prova,
                            "criado_por": usuario_id
                        }
                        res = supabase.table("mini_provas").insert(payload_prova).execute()
                        if res.data:
                            st.success(f"✅ Mini Prova '{titulo}' registrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar mini prova no banco: {e}")

    # Carrega as provas do professor para vincular as questões nas abas 2 e 3
    try:
        res_provas = supabase.table("mini_provas").select("id, titulo").eq("criado_por", usuario_id).execute()
        lista_provas = res_provas.data or []
    except Exception:
        lista_provas = []

    if not lista_provas:
        st.info("⚠️ Crie a definição de uma Mini Prova na Aba 1 antes de gerenciar questões.")
        return

    dict_provas = {p["titulo"]: p["id"] for p in lista_provas}

    # 📑 ABA 2: CADASTRO MANUAL DO ZERO (SEM OBRIGATORIEDADE DE ARQUIVO)
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
                        # 1. Insere na tabela 'questoes'
                        res_q = supabase.table("questoes").insert({"mini_prova_id": prova_id_m, "enunciado": enunciado_m.strip()}).execute()
                        q_id = res_q.data[0]["id"]
                        
                        # 2. Monta o lote de alternativas
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
                        st.success("✅ Questão individual criada do zero com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar questão: {e}")

    # 📑 ABA 3: IMPORTAÇÃO E PARSING DE PDF/WORD COM GRAVAÇÃO EM MASSA
    with aba_importacao:
        st.subheader("Upload e Mapeamento Inteligente")
        prova_selecionada_i = st.selectbox("Vincular à qual Mini Prova?", list(dict_provas.keys()), key="sb_import_p")
        prova_id_i = dict_provas[prova_selecionada_i]
        
        arquivo_anexo = st.file_uploader("Suba o arquivo das questões (PDF ou .docx):", type=["pdf", "docx"])
        
        if arquivo_anexo is not None:
            extensao = arquivo_anexo.name.split(".")[-1].lower()
            texto_extraido = extrair_texto_arquivo(arquivo_anexo, extensao)
            
            if texto_extraido:
                questoes_processadas = parsing_questoes_regex(texto_extraido)
                
                if questoes_processadas:
                    st.success(f"🎯 O sistema identificou com sucesso {len(questoes_processadas)} questões no arquivo!")
                    st.session_state.pool_questoes_importadas = questoes_processadas
                    
                    # Preview das questões mapeadas com seus respectivos gabaritos mapeados
                    for idx, q_map in enumerate(questoes_processadas):
                        with st.expander(f"📋 Questão {idx + 1} - Gabarito Detectado: [{q_map['gabarito']}]", expanded=False):
                            st.write(f"**Enunciado:** {q_map['enunciado']}")
                            for letra, texto_alt in q_map["alternativas"].items():
                                marca = "🟢 (Correta)" if letra == q_map["gabarito"] else ""
                                st.write(f"*{letra})* {texto_alt} {marca}")
                    
                    st.divider()
                    
                    # 🚀 Gravação direta usando o gabarito específico de cada item do dicionário
                    if st.button("💾 CONFIRMAR E SALVAR TODAS AS QUESTÕES NO BANCO DE DADOS", type="primary", use_container_width=True):
                        try:
                            sucessos = 0
                            for q_pool in st.session_state.pool_questoes_importadas:
                                # Insere a questão na tabela correspondente
                                res_q = supabase.table("questoes").insert({"mini_prova_id": prova_id_i, "enunciado": q_pool["enunciado"]}).execute()
                                q_id = res_q.data[0]["id"]
                                
                                # Insere o bloco relacional de alternativas
                                lote_alt = []
                                for idx, letra in enumerate(["A", "B", "C", "D", "E"]):
                                    texto_alt = q_pool["alternativas"].get(letra, "")
                                    if texto_alt:
                                        lote_alt.append({
                                            "questao_id": q_id,
                                            "texto": texto_alt,
                                            "ordem": idx + 1,
                                            "correta": (letra == q_pool["gabarito"])  # ✅ Puxa o gabarito dinâmico extraído
                                        })
                                if lote_alt:
                                    supabase.table("alternativas").insert(lote_alt).execute()
                                sucessos += 1
                                
                            st.success(f"🔥 Pronto! {sucessos} questões foram salvas no banco de dados com seus respectivos gabaritos!")
                            st.session_state.pop("pool_questoes_importadas", None)
                        except Exception as e:
                            st.error(f"Erro na inserção em massa no Supabase: {e}")
                else:
                    st.warning("⚠️ O texto foi extraído, mas nenhum padrão de questão (Questão X ou A, B, C...) foi localizado de forma clara.")
                    with St.expander("Ver texto bruto extraído", expanded=True):
                        st.text(texto_extraido)

    st.divider()
    if st.button("⬅️ Voltar ao Painel Geral", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()