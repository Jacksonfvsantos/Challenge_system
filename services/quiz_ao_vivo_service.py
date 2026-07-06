from database.conexao import supabase

def listar_quizzes():
    try:
        res = supabase.table("quizzes").select("*, usuarios(nome)").order("data_criacao", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def criar_quiz(titulo, usuario_id, disciplina, tema):
    try:
        res = supabase.table("quizzes").insert({
            "titulo": titulo.strip(),
            "criado_por": usuario_id,
            "disciplina": disciplina.strip(),
            "tema": tema.strip(),
            "status": "criado"
        }).execute()
        return {"sucesso": True, "mensagem": "Sala criada!"} if res.data else {"sucesso": False, "mensagem": "Erro."}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def deletar_quiz(quiz_id):
    try:
        perguntas = supabase.table("perguntas_quiz").select("id").eq("quiz_id", quiz_id).execute().data
        
        if perguntas:
            pergunta_ids = [p["id"] for p in perguntas]
            supabase.table("alternativas_quiz").delete().in_("pergunta_id", pergunta_ids).execute()
            supabase.table("perguntas_quiz").delete().eq("quiz_id", quiz_id).execute()
        supabase.table("respostas_quiz").delete().eq("quiz_id", quiz_id).execute()
        supabase.table("participantes_quiz").delete().eq("quiz_id", quiz_id).execute()

        res = supabase.table("quizzes").delete().eq("id", quiz_id).execute()
        
        return len(res.data) > 0
    except Exception as e:
        print(f"Erro ao deletar quiz: {e}")
        return False