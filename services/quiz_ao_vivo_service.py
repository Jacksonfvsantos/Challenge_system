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
        supabase.table("respostas_quiz").delete().eq("quiz_id", quiz_id).execute()
        supabase.table("participantes_quiz").delete().eq("quiz_id", quiz_id).execute()
        supabase.table("quizzes").delete().eq("id", quiz_id).execute()
        return True
    except Exception:
        return False