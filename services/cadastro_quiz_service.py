import json
from database.conexao import supabase

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

def cadastrar_pergunta_completa(quiz_id, enunciado, tempo_limite, alternativas, alternativa_correta_idx):
    try:
        res_ordem = supabase.table("perguntas_quiz").select("ordem").eq("quiz_id", quiz_id).execute()
        proxima_ordem = len(res_ordem.data) + 1 if res_ordem.data else 1

        res_pergunta = supabase.table("perguntas_quiz").insert({
            "quiz_id": quiz_id,
            "texto": enunciado.strip(),
            "enunciado": enunciado.strip(),
            "tempo_limite_segundos": int(tempo_limite),
            "ordem": proxima_ordem,
            "alternativas": alternativas,
            "indice_correto": int(alternativa_correta_idx)
        }).execute()

        if not res_pergunta.data:
            return {"sucesso": False, "mensagem": "Falha operacional ao obter retorno da pergunta inserida."}

        dados_p = res_pergunta.data
        pergunta_id = dados_p[0]["id"] if isinstance(dados_p, list) else dados_p.get("id")

        if not pergunta_id:
            return {"sucesso": False, "mensagem": "Não foi possível recuperar o ID gerado para vincular as alternativas."}

        lote_alternativas = []
        for i, texto_alt in enumerate(alternativas):
            lote_alternativas.append({
                "pergunta_id": pergunta_id,
                "texto": texto_alt.strip(),
                "correta": (i == int(alternativa_correta_idx)),
                "ordem": i + 1
            })

        supabase.table("alternativas_quiz").insert(lote_alternativas).execute()
        return {"sucesso": True, "mensagem": f"✨ Pergunta {proxima_ordem} salva com sucesso no caderno!"}

    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro operacional: {str(e)}"}

def gerar_questoes_quiz_com_ia(quiz_id: str, tema: str, quantidade: int, api_key: str) -> dict:
    if genai is None:
        return {"sucesso": False, "mensagem": "SDK 'google-genai' não está instalado."}
    if not api_key:
        return {"sucesso": False, "mensagem": "Chave API do Gemini não fornecida."}

    try:
        client = genai.Client(api_key=api_key)
        
        prompt_sistema = (
            "Você é um renomado professor de engenharia de computação. Gere questões inéditas e "
            "técnicas de múltipla escolha baseadas estritamente no tema fornecido pelo usuário. "
            "Cada questão deve conter um enunciado claro, 4 alternativas de respostas (A, B, C, D) "
            "e o índice da alternativa correta (sendo 0 para A, 1 para B, 2 para C e 3 para D)."
        )

        esquema_saida = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "perguntas": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "enunciado": types.Schema(type=types.Type.STRING),
                            "tempo_limite": types.Schema(type=types.Type.INTEGER),
                            "alternativa_correta_idx": types.Schema(type=types.Type.INTEGER, enum=[0, 1, 2, 3]),
                            "alternativas": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(type=types.Type.STRING)
                            )
                        },
                        required=["enunciado", "tempo_limite", "alternativa_correta_idx", "alternativas"]
                    )
                )
            },
            required=["perguntas"]
        )

        config = types.GenerateContentConfig(
            system_instruction=prompt_sistema,
            response_mime_type="application/json",
            response_schema=esquema_saida,
            temperature=0.7
        )

        conteudo_prompt = f"Gere {quantidade} questões complexas sobre o tema: {tema}"
        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=conteudo_prompt,
            config=config
        )
        
        dados = json.loads(resposta.text)
        perguntas_geradas = dados.get("perguntas", [])
        
        sucessos = 0
        for p in perguntas_geradas:
            res = cadastrar_pergunta_completa(
                quiz_id=quiz_id,
                enunciado=p["enunciado"],
                tempo_limite=p["tempo_limite"],
                alternativas=p["alternativas"],
                alternativa_correta_idx=p["alternativa_correta_idx"]
            )
            if res["sucesso"]:
                sucessos += 1
                
        return {"sucesso": True, "mensagem": f"🔥 {sucessos} questões geradas e injetadas com sucesso!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro na IA ou banco: {str(e)}"}