import streamlit as st
from pypdf import PdfReader
from docx import Document
import json
import google.generativeai as genai  # Certifique-se de configurar a API key se usar genai

def extrair_texto_pdf(arquivo_bytes):
    reader = PdfReader(arquivo_bytes)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text() + "\n"
    return texto

def extrair_texto_docx(arquivo_bytes):
    doc = Document(arquivo_bytes)
    texto = ""
    for paragraph in doc.paragraphs:
        texto += paragraph.text + "\n"
    return texto

def parsear_questoes_com_ia(texto_bruto):
    """
    Usa IA para interpretar o texto bagunçado do PDF/DOC e estruturar em JSON estável.
    """
    # Exemplo utilizando a biblioteca oficial do Google GenAI
    # Certifique-se de ter genai.configure(api_key=st.secrets["GEMINI_API_KEY"]) no boot do app
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Analise o texto abaixo que contém questões de múltipla escolha com alternativas e gabarito.
        Extraia todas as questões e retorne EXCLUSIVAMENTE um array JSON válido, sem formatação markdown (sem ```json), seguindo exatamente esta estrutura:
        [
          {{
            "enunciado": "Texto completo do enunciado da questão",
            "alternativas": [
              {{"texto": "Texto da alternativa A", "correta": false}},
              {{"texto": "Texto da alternativa B", "correta": true}},
              {{"texto": "Texto da alternativa C", "correta": false}},
              {{"texto": "Texto da alternativa D", "correta": false}}
            ]
          }}
        ]
        
        Texto das questões:
        {texto_bruto}
        """
        
        resposta = model.generate_content(prompt)
        # Limpa possíveis formatações que a IA envie por costume
        conteudo_limpo = resposta.text.replace("```json", "").replace("```", "").strip()
        return json.loads(conteudo_limpo)
    except Exception as e:
        st.error(f"Erro no processamento da IA: {e}")
        return None