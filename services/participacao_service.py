from database.conexao import supabase
from datetime import datetime

def participar_desafio(desafio_id, usuario_id):
    """Registra o aluno como participante de um desafio."""
    try:
        # Verifica se já existe inscrição para evitar duplicidade
        existente = supabase.table("participantes_desafio").select("id") \
            .eq("desafio_id", desafio_id).eq("usuario_id", usuario_id).execute()
        
        if existente.data:
            return False

        supabase.table("participantes_desafio").insert({
            "desafio_id": desafio_id,
            "usuario_id": usuario_id,
            "status": "participando"
        }).execute()
        return True
    except Exception as e:
        print(f"Erro ao participar: {e}")
        return False

def listar_participantes(desafio_id):
    """Lista todos os participantes e suas submissões de um desafio específico."""
    try:
        # Incluímos o campo 'submissao' na consulta para o professor visualizar
        resposta = supabase.table("participantes_desafio") \
            .select("*, usuarios(nome), submissao") \
            .eq("desafio_id", desafio_id).execute()
        return resposta.data or []
    except Exception:
        return []

def concluir_desafio(desafio_id, usuario_id, submissao_texto):
    """Atualiza o status para concluído e salva a submissão do aluno."""
    try:
        supabase.table("participantes_desafio").update({
            "status": "concluido",
            "submissao": submissao_texto,
            "concluido_em": datetime.now().isoformat()
        }).eq("desafio_id", desafio_id).eq("usuario_id", usuario_id).execute()
        return True
    except Exception as e:
        print(f"Erro ao concluir: {e}")
        return False

def cancelar_participacao(desafio_id, usuario_id):
    """Remove a inscrição do aluno no desafio."""
    try:
        supabase.table("participantes_desafio").delete() \
            .eq("desafio_id", desafio_id).eq("usuario_id", usuario_id).execute()
        return True
    except Exception:
        return False