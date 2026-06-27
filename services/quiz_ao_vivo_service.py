from database.conexao import supabase

def criar_quiz(titulo, usuario_id, disciplina, tema):
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
    try:
        res = supabase.table("quizzes").select("*, usuarios(nome)").order("created_at", descending=True).execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Erro operacional [listar_quizzes_ativos]: {e}")
        return []

def deletar_quiz(quiz_id):
    try:
        try:
            supabase.table("respostas_quiz").delete().eq("quiz_id", quiz_id).execute()
        except Exception as e_resp:
            print(f"⚠️ Nota: Sem respostas para limpar ou erro ignorado: {e_resp}")

        try:
            supabase.table("participantes_quiz").delete().eq("quiz_id", quiz_id).execute()
        except Exception as e_part:
            print(f"⚠️ Nota: Sem participantes para limpar ou erro ignorado: {e_part}")

        try:
            res_p = supabase.table("perguntas_quiz").select("id").eq("quiz_id", quiz_id).execute()
            if res_p.data:
                p_ids = [p["id"] for p in res_p.data]
                supabase.table("alternativas_quiz").delete().in_("pergunta_id", p_ids).execute()
        except Exception as e_alt:
            print(f"⚠️ Nota: Sem alternativas relacionais para limpar ou erro ignorado: {e_alt}")

        try:
            supabase.table("perguntas_quiz").delete().eq("quiz_id", quiz_id).execute()
        except Exception as e_perg:
            print(f"⚠️ Nota: Sem perguntas para limpar ou erro ignorado: {e_perg}")

        res = supabase.table("quizzes").delete(count="exact").eq("id", quiz_id).execute()
        if hasattr(res, "count") and res.count is not None:
            return res.count > 0
        return True
    except Exception as e:
        print(f"❌ Erro crítico operacional [deletar_quiz]: {e}")
        return False