from database.conexao import supabase

def criar_quiz(titulo, usuario_id, disciplina, tema):
    """
    Cadastra um novo quiz síncrono no banco de dados.
    """
    try:
        res = supabase.table("quizzes").insert({
            "titulo": titulo.strip(),
            "criado_por": usuario_id,
            "disciplina": disciplina.strip(), # Tratando como string livre relacional
            "tema": tema.strip(),
            "status": "criado" # Garante o estado inicial
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
    Remove um quiz específico do banco de dados.
    """
    try:
        res = supabase.table("quizzes").delete().eq("id", quiz_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro operacional [deletar_quiz]: {e}")
        return False