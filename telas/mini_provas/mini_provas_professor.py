import streamlit as st
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
import io

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
                st.error("❌ Erro: O pacote 'pypdf' não está instalado. Adicione-o ao requirements.txt.")
                return ""
            leitor = PdfReader(io.BytesIO(arquivo_subido.read()))
            for pagina in leitor.pages:
                texto_bruto += pagina.extract_text() + "\n"
        elif extensao == "docx":
            if Document is None:
                st.error("❌ Erro: O pacote 'python-docx' não está instalado. Adicione-o ao requirements.txt.")
                return ""
            doc = Document(io.BytesIO(arquivo_subido.read()))
            for paragrafo in doc.paragraphs:
                texto_bruto += paragrafo.text + "\n"
    except Exception as e:
        st.error(f"Erro ao processar a leitura do arquivo: {e}")
    return texto_bruto

def tela_mini_provas_professor():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    
    cabecalho("Painel do Docente: Gestão de Mini Provas", "Cadastre novos exames e gerencie avaliações")

    if not usuario_id:
        st.error("Sessão de usuário inválida ou expirada.")
        return

    # 📋 ABAS DE CONFIGURAÇÃO
    aba_cadastro, aba_importacao = st.tabs(["📝 Configurar Escopo da Prova", "📂 Importar Questões via PDF/Word"])

    # 📑 ABA 1: CONFIGURAÇÃO DE METADADOS DA PROVA
    with aba_cadastro:
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
                        # Payload casado perfeitamente com a tabela public.mini_provas do seu DDL
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
                            st.success(f"✅ Mini Prova '{titulo}' registrada com sucesso no banco de dados!")
                            st.info("💡 Prossiga para a aba ao lado para fazer upload de questões para este exame.")
                    except Exception as e:
                        st.error(f"Erro ao salvar mini prova no banco: {e}")

    # 📑 ABA 2: IMPORTAÇÃO E PARSING DE PDF/WORD
    with aba_importacao:
        st.subheader("Upload de Caderno de Questões")
        st.caption("Selecione a mini-prova de destino e suba o arquivo contendo os enunciados e alternativas.")
        
        # Carrega as provas do professor para vinculação da chave estrangeira
        try:
            res_provas = supabase.table("mini_provas").select("id, titulo").eq("criado_por", usuario_id).execute()
            lista_provas = res_provas.data or []
        except Exception as e:
            st.error(f"Erro ao carregar mini-provas: {e}")
            lista_provas = []
            
        if not lista_provas:
            st.info("⚠️ Você precisa criar a definição de pelo menos uma Mini Prova na aba ao lado antes de subir arquivos.")
        else:
            dict_provas = {p["titulo"]: p["id"] for p in lista_provas}
            prova_selecionada = st.selectbox("Selecione a Mini Prova de destino:", list(dict_provas.keys()))
            prova_id_alvo = dict_provas[prova_selecionada]
            
            arquivo_anexo = st.file_uploader("Suba o arquivo das questões (PDF ou Word .docx):", type=["pdf", "docx"])
            
            if arquivo_anexo is not None:
                extensao = arquivo_anexo.name.split(".")[-1].lower()
                
                with st.spinner("Lendo e interpretando o texto do arquivo..."):
                    texto_extraido = extrair_texto_arquivo(arquivo_anexo, extensao)
                    
                if texto_extraido:
                    st.success("📝 Texto extraído com sucesso!")
                    with st.expander("🔍 Visualizar Texto Extraído para Verificação", expanded=False):
                        st.text_area("Conteúdo Bruto:", texto_extraido, height=250)
                        
                    st.info("💡 Você pode colar e segmentar as questões no formulário de cadastro direto do banco a partir deste texto.")
                else:
                    st.error("❌ Não foi possível extrair texto legível deste documento. Verifique se ele não é uma imagem digitalizada.")

    st.divider()
    if st.button("⬅️ Voltar ao Painel Geral", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()