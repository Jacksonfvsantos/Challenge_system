from database.conexao import supabase

# Dentro de services/cadastro_quiz_service.py

def cadastrar_pergunta_completa(quiz_id, enunciado, tempo_limite, alternativas, alternativa_correta_idx):
    try:
        # 1. Descobrir a próxima ordem para este quiz específico
        res_ordem = supabase.table("perguntas_quiz").select("ordem").eq("quiz_id", quiz_id).execute()
        proxima_ordem = len(res_ordem.data) + 1 if res_ordem.data else 1

        # 2. Inserir a Pergunta tratando todas as colunas legadas obrigatórias
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

        # ✅ CAPTURA BLINDADA DO ID DA PERGUNTA:
        # Aceita se vier como lista de um dicionário ou objeto direto
        dados_p = res_pergunta.data
        pergunta_id = dados_p[0]["id"] if isinstance(dados_p, list) else dados_p.get("id")

        if not pergunta_id:
            return {"sucesso": False, "mensagem": "Não foi possível recuperar o ID gerado para vincular as alternativas."}

        # 3. Preparar o lote (bulk) de alternativas para a nova tabela relacional
        lote_alternativas = []
        for i, texto_alt in enumerate(alternativas):
            lote_alternativas.append({
                "pergunta_id": pergunta_id, # <-- Agora garantido!
                "texto": texto_alt.strip(),
                "correta": (i == int(alternativa_correta_idx)),
                "ordem": i + 1
            })

        # 4. Inserir todas as alternativas de uma vez só no banco
        supabase.table("alternativas_quiz").insert(lote_alternativas).execute()

        return {"sucesso": True, "mensagem": f"✨ Pergunta {proxima_ordem} salva com sucesso no caderno!"}

    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro operacional: {str(e)}"}