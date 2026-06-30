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
            "disciplina": disciplina.strip() if disciplina else None,
            "tema": tema.strip() if tema else None,
            "status": "criado"
        }).execute()
        return {"sucesso": True, "mensagem": "Sala de Quiz ativada!"} if res.data else {"sucesso": False, "mensagem": "Erro ao criar."}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def deletar_quiz(quiz_id):
    try:
        # Limpeza relacional em cascata
        supabase.table("respostas_quiz").delete().eq("quiz_id", quiz_id).execute()
        supabase.table("participantes_quiz").delete().eq("quiz_id", quiz_id).execute()
        
        res_p = supabase.table("perguntas_quiz").select("id").eq("quiz_id", quiz_id).execute()
        if res_p.data:
            p_ids = [p["id"] for p in res_p.data]
            supabase.table("alternativas_quiz").delete().in_("pergunta_id", p_ids).execute()
            supabase.table("perguntas_quiz").delete().eq("quiz_id", quiz_id).execute()
            
        supabase.table("quizzes").delete().eq("id", quiz_id).execute()
        return True
    except Exception:
        return False

def atualizar_status_quiz(quiz_id, novo_status):
    try:
        res = supabase.table("quizzes").update({"status": novo_status}).eq("id", quiz_id).execute()
        return bool(res.data)
    except Exception:
        return False