import io
import json
from google import genai
from google.genai import types
from pypdf import PdfReader
from docx import Document

def extrair_texto_de_arquivo(arquivo_bytes, extensao):
    texto = ""
    try:
        if extensao == "pdf":
            leitor = PdfReader(io.BytesIO(arquivo_bytes))
            for p in leitor.pages: texto += (p.extract_text() or "") + "\n"
        elif extensao == "docx":
            doc = Document(io.BytesIO(arquivo_bytes))
            for p in doc.paragraphs: texto += p.text + "\n"
    except Exception as e:
        print(f"Erro na extração: {e}")
    return texto

def gerar_questoes_ia(texto_base, prompt_adicional, api_key, tipo="quiz"):
    client = genai.Client(api_key=api_key)

    esquema = types.Schema(type=types.Type.OBJECT, properties={
        "questoes": types.Schema(type=types.Type.ARRAY, items=types.Schema(
            type=types.Type.OBJECT, properties={
                "enunciado": types.Schema(type=types.Type.STRING),
                "alternativas": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                "correta_idx": types.Schema(type=types.Type.INTEGER)
            }, required=["enunciado", "alternativas", "correta_idx"]
        ))
    })
    
    prompt = f"Baseado no texto: {texto_base[:8000]}. Instrução extra: {prompt_adicional}"
    resposta = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=esquema)
    )
    return json.loads(resposta.text).get("questoes", [])