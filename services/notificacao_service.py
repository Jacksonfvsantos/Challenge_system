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
