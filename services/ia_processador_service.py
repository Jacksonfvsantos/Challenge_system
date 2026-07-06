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

def gerar_questoes_ia(texto_base, prompt_adicional, api_key):
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

import json
from google import genai
from google.genai import types

def gerar_questoes_ia_multimodal(arquivo_bytes, mime_type, prompt_custom, api_key):
    """Envia o arquivo cru para o Gemini ler visualmente (incluindo imagens e prints de código)."""
    try:
        client = genai.Client(api_key=api_key)
        
        # Instrução rigorosa para a IA focar nas imagens
        prompt_sistema = """Você é um especialista em criar questões de múltipla escolha para competições acadêmicas.
Sua tarefa é ler o documento fornecido VISUALMENTE. 
MUITO IMPORTANTE: O documento contém imagens (prints) com trechos de código. VOCÊ DEVE ler o código dentro dessas imagens e gerar questões técnicas baseadas neles."""
        
        if prompt_custom:
            prompt_sistema += f"\n\nInstruções extras do professor: {prompt_custom}"
            
        # Garante a estrutura exata para o banco de dados
        esquema_saida = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "perguntas": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "enunciado": types.Schema(type=types.Type.STRING),
                            "correta_idx": types.Schema(type=types.Type.INTEGER),
                            "alternativas": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING))
                        },
                        required=["enunciado", "correta_idx", "alternativas"]
                    )
                )
            },
            required=["perguntas"]
        )

        config = types.GenerateContentConfig(
            system_instruction=prompt_sistema,
            response_mime_type="application/json",
            response_schema=esquema_saida,
            temperature=0.5
        )
        
        # Prepara o arquivo diretamente da memória para o modelo
        documento_part = types.Part.from_bytes(
            data=arquivo_bytes,
            mime_type=mime_type
        )
        
        conteudo_prompt = "Leia este documento e gere as questões (lembre-se de interpretar os códigos dentro das imagens)."
        
        # Faz a chamada multimodal
        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[documento_part, conteudo_prompt],
            config=config
        )
        
        dados = json.loads(resposta.text)
        return dados.get("perguntas", [])
        
    except Exception as e:
        print(f"Erro na IA Multimodal: {e}")
        return []