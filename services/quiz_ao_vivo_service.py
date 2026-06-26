from database.conexao import supabase

def criar_quiz(titulo, usuario_id, disciplina, tema):
    """
    Cadastra um novo quiz síncrono no banco de dados.
    """
    try:
        res = supabase.table("quizzes").insert({
            "titulo": titulo.strip(),
            "criado_por": usuario_id,
            "disciplina": disciplina.strip() if disciplina else None,
            "tema": tema.strip() if tema else None,
            "status": "criado"
        }).execute()
        
        if res.data:
            return {"sucesso": True, "mensagem": "Sala de Quiz ativada com sucesso!"}
        return {"sucesso": False, "mensagem": "Não foi possível registrar o quiz no banco."}
    except Exception as e:
        print(f"❌ Erro operacional [criar_quiz]: {e}")
        return {"sucesso": False, "mensagem": f"Erro interno: {e}"}

def listar_quizzes_ativos():
    """
    Busca a lista de todos os quizzes cadastrados no ecossistema.
    """
    try:
        res = supabase.table("quizzes").select("*, usuarios(nome)").order("created_at", descending=True).execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Erro operacional [listar_quizzes_ativos]: {e}")
        return []

def deletar_quiz(quiz_id):
    """
    Remove um quiz específico do banco de dados fazendo a limpeza prévia 
    de todas as tabelas amarradas a ele para evitar violação de Foreign Key.
    """
    try:
        # 1. Apaga primeiro as respostas vinculadas a este quiz
        try:
            supabase.table("respostas_quiz").delete().eq("quiz_id", quiz_id).execute()
        except Exception as e_resp:
            print(f"⚠️ Nota: Sem respostas para limpar ou erro ignorado: {e_resp}")

        # 2. Apaga os participantes vinculados a este quiz
        try:
            supabase.table("participantes_quiz").delete().eq("quiz_id", quiz_id).execute()
        except Exception as e_part:
            print(f"⚠️ Nota: Sem participantes para limpar ou erro ignorado: {e_part}")

        # 3. Apaga as alternativas das perguntas deste quiz (se houver a amarração direta)
        try:
            # Busca os IDs das perguntas deste quiz
            res_p = supabase.table("perguntas_quiz").select("id").eq("quiz_id", quiz_id).execute()
            if res_p.data:
                p_ids = [p["id"] for p in res_p.data]
                # Limpa as alternativas associadas a essas perguntas
                supabase.table("alternativas_quiz").delete().in_("pergunta_id", p_ids).execute()
        except Exception as e_alt:
            print(f"⚠️ Nota: Sem alternativas relacionais para limpar ou erro ignorado: {e_alt}")

        # 4. Apaga as perguntas vinculadas a este quiz
        try:
            supabase.table("perguntas_quiz").delete().eq("quiz_id", quiz_id).execute()
        except Exception as e_perg:
            print(f"⚠️ Nota: Sem perguntas para limpar ou erro ignorado: {e_perg}")

        # 5. Agora que o quiz está totalmente isolado e livre de amarras, faz o delete dele
        res = supabase.table("quizzes").delete(count="exact").eq("id", quiz_id).execute()
        
        if hasattr(res, "count") and res.count is not None:
            return res.count > 0
        return True

    except Exception as e:
        print(f"❌ Erro crítico operacional [deletar_quiz]: {e}")
        return False