from database.conexao import supabase
from datetime import datetime

def participar_desafio(desafio_id, usuario_id):
    existente = (
        supabase
        .table("participantes_desafio")
        .select("*")
        .eq("desafio_id", desafio_id)
        .eq("usuario_id", usuario_id)
        .execute()
    )

    if existente.data:
        return False

    supabase.table("participantes_desafio").insert({
        "desafio_id": desafio_id,
        "usuario_id": usuario_id,
        "status": "participando"
    }).execute()
    return True

def eh_uuid_valido(valor):
    return valor and str(valor).strip() != "None" and str(valor).strip() != ""

def listar_participantes(desafio_id):
    if not eh_uuid_valido(desafio_id):
        return []
    try:
        res = supabase.table("participantes_desafio").select("*, usuarios(nome)").eq("desafio_id", str(desafio_id)).execute()
        return res.data
    except Exception as e:
        print(f"Erro no Supabase: {e}")
        return []

def concluir_desafio(desafio_id, usuario_id):
    supabase.table("participantes_desafio").update({
        "status": "concluido",
        "concluido_em": datetime.now().isoformat()
    }).eq("desafio_id", desafio_id).eq("usuario_id", usuario_id).execute()

    participantes = (
        supabase
        .table("participantes_desafio")
        .select("*")
        .eq("desafio_id", desafio_id)
        .execute()
    )

    todos_concluidos = all(p["status"] == "concluido" for p in participantes.data)
    if todos_concluidos:
        supabase.table("desafios").update({"status": "concluido"}).eq("id", desafio_id).execute()

def cancelar_participacao(desafio_id, usuario_id):
    supabase.table("participantes_desafio").delete().eq("desafio_id", desafio_id).eq("usuario_id", usuario_id).execute()