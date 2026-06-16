from typing import Dict, Any

def criar_quiz(titulo: str, professor_id: str, disciplina_nome: str = "", tema: str = "") -> Dict[str, Any]:
    """Cria um novo quiz associando-o opcionalmente a uma disciplina e temas específicos."""
    titulo = titulo.strip() if titulo else ""
    if len(titulo) < 3:
        return {"sucesso": False, "mensagem": "O título do quiz deve ter pelo menos 3 caracteres."}

    # Resolve o ID da disciplina dinamicamente reaproveitando o service unificado
    disciplina_id = None
    if disciplina_nome.strip():
        try:
            from services.mini_prova_service import buscar_ou_criar_disciplina
            disc_db = buscar_ou_criar_disciplina(disciplina_nome)
            disciplina_id = disc_db.get("id")
        except Exception:
            pass

    novo_quiz = {
        "titulo": titulo,
        "criado_por": str(professor_id).strip(),
        "status": "criado",
        "pergunta_atual": 0,
        "disciplina_id": dsciplina_id,  
        "tema": tema.strip() if tema else None  
    }

    try:
        # Executa a chamada do insert na tabela de quizzes do Supabase
        from database.conexao import supabase
        resposta = supabase.table("quizzes").insert(novo_quiz).execute()
        if resposta.data:
            return {"sucesso": True, "dados": resposta.data[0], "mensagem": "Quiz configurado e registrado com sucesso!"}
        return {"sucesso": False, "mensagem": "Não foi possível registrar o quiz no servidor."}
    except Exception as exc:
        return {"sucesso": False, "mensagem": f"Erro inesperado de comunicação: {str(exc)}"}