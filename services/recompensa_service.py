from database.conexao import supabase
from database.conexao import supabase
from services.notificacao_service import criar_notificacao

def listar_recompensas():
    try:
        res = supabase.table("recompensas").select("*").order("created_at").execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Erro [listar_recompensas]: {e}")
        return []

def criar_recompensa(titulo, descricao, custo_pontos, tipo, usuario_id):
    try:
        res = supabase.table("recompensas").insert({
            "titulo": titulo.strip(),
            "descricao": descricao.strip(),
            "custo_pontos": int(custo_pontos),
            "tipo": tipo,
            "criado_por": usuario_id
        }).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro [criar_recompensa]: {e}")
        return False

def editar_recompensa(recompensa_id, novo_titulo, nova_descricao, novo_custo, novo_tipo):
    try:
        res = supabase.table("recompensas").update({
            "titulo": novo_titulo.strip(),
            "descricao": nova_descricao.strip(),
            "custo_pontos": int(novo_custo),
            "tipo": novo_tipo
        }).eq("id", recompensa_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro [editar_recompensa]: {e}")
        return False

def deletar_recompensa(recompensa_id):
    try:
        res = supabase.table("recompensas").delete().eq("id", recompensa_id).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro [deletar_recompensa]: {e}")
        return False
    
def solicitar_resgate(recompensa_id, aluno_id):
    try:
        existe = supabase.table("historico_recompensas")\
            .select("id")\
            .eq("recompensa_id", recompensa_id)\
            .eq("aluno_id", aluno_id)\
            .eq("status", "pendente")\
            .execute()
            
        if existe.data:
            return {"sucesso": False, "mensagem": "Você já possui uma solicitação pendente para esta recompensa."}

        res = supabase.table("historico_recompensas").insert({
            "recompensa_id": recompensa_id,
            "aluno_id": aluno_id,
            "status": 'pendente'
        }).execute()
        return {"sucesso": True, "mensagem": "Solicitação enviada! Aguarde a aprovação do professor."}
    except Exception as e:
        print(f"❌ Erro [solicitar_resgate]: {e}")
        return {"sucesso": False, "mensagem": "Erro operacional ao solicitar resgate."}

def listar_solicitacoes_pendentes():
    try:
        res = supabase.table("historico_recompensas")\
            .select("*, usuarios(nome), recompensas(titulo, custo_pontos)")\
            .eq("status", "pendente")\
            .execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Erro [listar_solicitacoes_pendentes]: {e}")
        return []

def alterar_status_solicitacao(solicitacao_id, novo_status):
    try:
        solicitacao = supabase.table("historico_recompensas").select("aluno_id, recompensas(titulo)").eq("id", solicitacao_id).single().execute()
        
        if not solicitacao.data:
            return False
            
        aluno_id = solicitacao.data["aluno_id"]
        item = solicitacao.data["recompensas"]["titulo"]

        res = supabase.table("historico_recompensas").update({"status": novo_status}).eq("id", solicitacao_id).execute()
        
        if res.data:
            msg = f"Sua solicitação do item '{item}' foi {novo_status}!"

            criar_notificacao(usuario_id=aluno_id, titulo="Atualização de Resgate", mensagem=msg)
            
        return len(res.data) > 0
    except Exception as e:
        print(f"❌ Erro [alterar_status_solicitacao]: {e}")
        return False