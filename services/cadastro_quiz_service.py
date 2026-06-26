from database.conexao import supabase

def cadastrar_pergunta_completa(quiz_id, enunciado, tempo_limite, alternativas, alternativa_correta_idx):
    """
    Cadastra uma pergunta e suas 4 alternativas vinculadas no banco.
    alternativas: lista de 4 strings
    alternativa_correta_idx: int (0 a 3) indicando qual é a correta
    """
    try:
        # 1. Descobrir a próxima ordem da pergunta para esse quiz
        res_ordem = supabase.table("perguntas_quiz").select("ordem").eq("quiz_id", quiz_id).execute()
        proxima_ordem = len(res_ordem.data) + 1 if res_ordem.data else 1

        # 2. Inserir a Pergunta tratando todas as colunas antigas obrigatórias
        res_pergunta = supabase.table("perguntas_quiz").insert({
            "quiz_id": quiz_id,
            "texto": enunciado.strip(),
            "enunciado": enunciado.strip(),
            "tempo_limite_segundos": int(tempo_limite),
            "ordem": proxima_ordem,
            "alternativas": alternativas,
            "indice_correto": int(alternativa_correta_idx)  # ✅ SOLUÇÃO: Preenche a coluna faltante do banco antigo
        }).execute()

        if not res_pergunta.data:
            return {"sucesso": False, "mensagem": "Falha ao registrar a estrutura da pergunta."}

        pergunta_id = res_pergunta.data[0]["id"]

        # 3. Inserir as 4 Alternativas
        payload_alternativas = []
        for idx, texto_alt in enumerate(alternativas):
            payload_alternativas.append({
                "pergunta_id": pergunta_id,
                "texto": texto_alt.strip(),
                "correta": (idx == alternativa_correta_idx),
                "ordem": idx + 1
            })

        res_alt = supabase.table("alternativas_quiz").insert(payload_alternativas).execute()
        
        if res_alt.data:
            return {"sucesso": True, "mensagem": f"Pergunta {proxima_ordem} salva com sucesso!"}
        
        return {"sucesso": False, "mensagem": "Erro ao salvar as alternativas da pergunta."}

    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro operacional: {e}"}