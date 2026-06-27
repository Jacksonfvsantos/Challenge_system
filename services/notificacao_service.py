from database.conexao import supabase

def registrar_log_seguranca(usuario_id: str, acao: str, tabela_alvo: str, detalhes: dict, ip_address: str = "0.0.0.0") -> bool:
    try:
        payload = {
            "usuario_id": usuario_id,
            "acao": acao,
            "tabela_alvo": tabela_alvo,
            "detalhes": detalhes,
            "ip_address": ip_address
        }
        res = supabase.table("logs_auditoria").insert(payload).execute()
        return bool(res.data)
    except Exception as e:
        print(f"❌ Falha ao gravar log de auditoria: {e}")
        return False

def criar_notificacao(usuario_id: str, titulo: str, mensagem: str) -> bool:
    try:
        payload = {
            "usuario_id": usuario_id,
            "titulo": titulo.strip(),
            "mensagem": mensagem.strip(),
            "lida": False
        }
        res = supabase.table("notificacoes").insert(payload).execute()
        return bool(res.data)
    except Exception as e:
        print(f"❌ Erro ao criar notificacao: {e}")
        return False

def listar_notificacoes_usuario(usuario_id: str, apenas_nao_lidas: bool = False) -> list:
    try:
        query = supabase.table("notificacoes").select("*").eq("usuario_id", usuario_id)
        if apenas_nao_lidas:
            query = query.eq("lida", False)
        res = query.order("criado_em", descending=True).execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Erro ao listar notificacoes: {e}")
        return []

def marcar_notificacao_como_lida(notificacao_id: str) -> bool:
    try:
        res = supabase.table("notificacoes").update({"lida": True}).eq("id", notificacao_id).execute()
        return bool(res.data)
    except Exception as e:
        print(f"❌ Erro ao atualizar notificacao: {e}")
        return False