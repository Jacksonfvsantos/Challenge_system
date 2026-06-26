import streamlit as st
import json
from pypdf import PdfReader
from docx import Document
import google.generativeai as genai

def extrair_texto_pdf(arquivo_bytes):
    try:
        reader = PdfReader(arquivo_bytes)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        return ""

def extrair_texto_docx(arquivo_bytes):
    try:
        doc = Document(arquivo_bytes)
        texto = ""
        for paragraph in doc.paragraphs:
            texto += paragraph.text + "\n"
        return texto
    except Exception as e:
        st.error(f"Erro ao ler DOCX: {e}")
        return ""

def parsear_questoes_com_ia(texto_bruto):
    """
    Envia o texto extraído para a nova API do Gemini 2.5 estruturar estritamente como JSON válido.
    """
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("🛑 API Key 'GEMINI_API_KEY' não configurada nos Secrets do Streamlit Cloud.")
        return None

    try:
        genai.configure(api_key=api_key)
        
        # 🚀 ATUALIZAÇÃO TECNOLÓGICA: Substituído o modelo descontinuado pelo novo Gemini 2.5 Flash
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Você é um assistente de engenharia de software especializado em estruturar dados.
        Analise o texto abaixo, que contém questões de múltipla escolha com alternativas e gabarito indicador.
        
        Extraia todas as questões localizadas e retorne EXCLUSIVAMENTE um array JSON puro (sem markdown, sem ```json), seguindo rigorosamente esta estrutura:
        [
          {{
            "enunciado": "Enunciado completo da questão",
            "alternativas": [
              {{"texto": "Texto da opção A", "correta": false}},
              {{"texto": "Texto da opção B", "correta": true}},
              {{"texto": "Texto da opção C", "correta": false}},
              {{"texto": "Texto da opção D", "correta": false}}
            ]
          }}
        ]
        
        Texto bruto extraído do arquivo:
        {texto_bruto}
        """
        
        resposta = model.generate_content(prompt)
        conteudo_limpo = resposta.text.replace("```json", "").replace("```", "").strip()
        return json.loads(conteudo_limpo)
    except Exception as e:
        st.error(f"Falha na interpretação da inteligência artificial: {e}")
        return None