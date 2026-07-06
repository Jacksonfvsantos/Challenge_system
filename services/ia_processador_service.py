import json
from google import genai
from google.genai import types

def gerar_questoes_ia_multimodal(arquivo_bytes, mime_type, prompt_custom, api_key):
    """Envia o arquivo cru para o Gemini ler visualmente, forçando a separação estrita de alternativas."""
    try:
        client = genai.Client(api_key=api_key)
        
        prompt_sistema = """Você é um especialista em criar questões de múltipla escolha para competições de tecnologia.
Sua tarefa é ler o documento fornecido VISUALMENTE. O documento contém imagens (prints) com trechos de código.

REGRAS CRÍTICAS DE FORMATAÇÃO:
1. O campo 'enunciado' DEVE conter APENAS o contexto da pergunta e o trecho de código (se houver). NUNCA coloque as opções de resposta dentro do texto do enunciado.
2. O campo 'alternativas' DEVE ser uma lista contendo EXATAMENTE o texto de cada opção de resposta. Não retorne uma lista vazia e não use apenas letras soltas (ex: NUNCA faça ["A", "B", "C", "D"]). Extraia o conteúdo real de cada opção.
3. Se a imagem contiver as opções, recorte-as do texto principal e mova-as exclusivamente para o array 'alternativas'."""
        
        if prompt_custom:
            prompt_sistema += f"\n\nInstruções extras do professor: {prompt_custom}"
            
        esquema_saida = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "questoes": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "enunciado": types.Schema(type=types.Type.STRING),
                            "correta_idx": types.Schema(type=types.Type.INTEGER),
                            "alternativas": types.Schema(
                                type=types.Type.ARRAY, 
                                items=types.Schema(type=types.Type.STRING),
                                description="Lista com as 4 opções de resposta formatadas em texto completo."
                            )
                        },
                        required=["enunciado", "correta_idx", "alternativas"]
                    )
                )
            },
            required=["questoes"]
        )

        config = types.GenerateContentConfig(
            system_instruction=prompt_sistema,
            response_mime_type="application/json",
            response_schema=esquema_saida,
            temperature=0.3  # Temperatura baixa para evitar que a IA invente formatos
        )
        
        documento_part = types.Part.from_bytes(
            data=arquivo_bytes,
            mime_type=mime_type
        )
        
        conteudo_prompt = "Leia este documento visualmente e gere as questões seguindo as regras críticas de separação de alternativas."
        
        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[documento_part, conteudo_prompt],
            config=config
        )
        
        dados = json.loads(resposta.text)
        return dados.get("questoes", [])
        
    except Exception as e:
        print(f"Erro na IA Multimodal: {e}")
        return []