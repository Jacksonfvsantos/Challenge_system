from database.conexao import supabase

def criar_quiz(titulo, usuario_id, disciplina_id, tema):
    """
    Cadastra um novo quiz síncrono associado a uma disciplina e a um tema específico.
    """
    try:
        # ✅ CORREÇÃO: Variável mapeada corretamente com todas as letras 'i'
        res = supabase.table("quizzes").insert({
            "titulo": titulo.strip(),
            "criado_por": usuario_id,
            "disciplina_id": disciplina_id,
            "tema": tema.strip()
        }).execute()
        
        return res.data if res.data else []
    except Exception as e:
        print(f"❌ Erro operacional [criar_quiz]: {e}")
        return []

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
    Remove um quiz específico do banco de dados (as chaves estrangeiras cuidam do cascade).
    """
    try:
        res = supabase.table("quizzes").delete().eq("id", quiz_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro operacional [deletar_quiz]: {e}")
        return False
