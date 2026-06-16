from database.conexao import supabase

# --------------------------------------------------
# GERENCIAMENTO DE TIMES (Aba: times.py)
# --------------------------------------------------

def criar_time(nome: str) -> bool:
    """Insere uma nova equipe na tabela 'times' do Supabase de forma segura."""
    if not nome or not nome.strip():
        return False
        
    try:
        payload = {"nome": nome.strip()}
        resposta = supabase.table("times").insert(payload).execute()
        
        if resposta.data and len(resposta.data) > 0:
            return True
        return False
    except Exception as erro:
        print(f"❌ Erro [criar_time]: {erro}")
        return False


def listar_times():
    """Busca a lista de todos os times cadastrados no sistema."""
    try:
        resposta = supabase.table("times").select("*").order("nome").execute()
        return resposta.data or []
    except Exception as erro:
        print(f"❌ Erro [listar_times]: {erro}")
        return []


def editar_time(time_id: str, novo_nome: str) -> bool:
    """Atualiza o nome de um time existente identificando-o via UUID."""
    if not str(time_id).strip() or not novo_nome or not novo_nome.strip():
        return False
    try:
        resposta = (
            supabase
            .table("times")
            .update({"nome": novo_nome.strip()})
            .eq("id", str(time_id).strip())
            .execute()
        )
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [editar_time]: {erro}")
        return False


def deletar_time(time_id: str) -> bool:
    """Exclui um time do banco de dados com base no seu UUID."""
    if not str(time_id).strip():
        return False
    try:
        # Nota: Se houver membros vinculados, a tabela 'time_membros' limpa em cascata 
        # ou precisará ser limpa antes dependendo das restrições do seu banco.
        resposta = (
            supabase
            .table("times")
            .delete()
            .eq("id", str(time_id).strip())
            .execute()
        )
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [deletar_time]: {erro}")
        return False


# --------------------------------------------------
# VÍNCULOS DE ALUNOS (Aba: integrantes.py)
# --------------------------------------------------

def aluno_tem_time(usuario_id: str) -> bool:
    """Verifica se um determinado aluno já está associado a alguma equipe."""
    if not str(usuario_id).strip():
        return False
    try:
        resposta = (
            supabase
            .table("time_membros")
            .select("id")
            .eq("usuario_id", str(usuario_id).strip())
            .execute()
        )
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [aluno_tem_time]: {erro}")
        return False


def entrar_no_time(time_id: str, usuario_id: str) -> bool:
    """Permite que um próprio aluno ingresse voluntariamente em uma equipe livre."""
    if not str(time_id).strip() or not str(usuario_id).strip():
        return False
        
    if aluno_tem_time(usuario_id):
        return False
        
    try:
        payload = {
            "time_id": str(time_id).strip(),
            "usuario_id": str(usuario_id).strip()
        }
        resposta = supabase.table("time_membros").insert(payload).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [entrar_no_time]: {erro}")
        return False


def listar_membros_time(time_id: str):
    """Retorna os dados cadastrais completos dos usuários pertencentes a um time."""
    if not str(time_id).strip():
        return []
    try:
        resposta = (
            supabase
            .table("time_membros")
            .select("usuario_id, usuarios(id, nome, email)")
            .eq("time_id", str(time_id).strip())
            .execute()
        )
        
        membros = []
        if resposta.data:
            for item in resposta.data:
                user_data = item.get("usuarios")
                if isinstance(user_data, dict):
                    membros.append({
                        "id": user_data.get("id"),
                        "nome": user_data.get("nome"),
                        "email": user_data.get("email")
                    })
        return membros
    except Exception as erro:
        print(f"❌ Erro [listar_membros_time]: {erro}")
        return []


def listar_alunos():
    """Busca todos os usuários com perfil de estudante para alocação do professor."""
    try:
        resposta = (
            supabase
            .table("usuarios")
            .select("id, nome, email")
            .eq("tipo_usuario", "aluno")
            .order("nome")
            .execute()
        )
        return resposta.data or []
    except Exception as erro:
        print(f"❌ Erro [listar_alunos]: {erro}")
        return []


def adicionar_aluno(time_id: str, usuario_id: str) -> bool:
    """Vincula administrativamente (ação do professor) um aluno a um determinado time."""
    return entrar_no_time(time_id, usuario_id)


def remover_aluno(time_id: str, usuario_id: str) -> bool:
    """Remove a associação de um aluno específico com sua equipe atual."""
    if not str(time_id).strip() or not str(usuario_id).strip():
        return False
    try:
        resposta = (
            supabase
            .table("time_membros")
            .delete()
            .eq("time_id", str(time_id).strip())
            .eq("usuario_id", str(usuario_id).strip())
            .execute()
        )
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [remover_aluno]: {erro}")
        return False


def mover_aluno(usuario_id: str, destino_time_id: str) -> bool:
    """Transfere a alocação de um estudante para um novo time de destino."""
    if not str(usuario_id).strip() or not str(destino_time_id).strip():
        return False
    try:
        # 1. Remove dos times antigos que porventura faça parte
        supabase.table("time_membros").delete().eq("usuario_id", str(usuario_id).strip()).execute()
        
        # 2. Insere na nova equipe escolhida
        payload = {
            "time_id": str(destino_time_id).strip(),
            "usuario_id": str(usuario_id).strip()
        }
        resposta = supabase.table("time_membros").insert(payload).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [mover_aluno]: {erro}")
        return False


# --------------------------------------------------
# CONFIGURAÇÃO DE BATALHAS (Aba: gerenciar_batalhas.py)
# --------------------------------------------------

def listar_batalhas():
    """Busca o histórico de batalhas registradas no banco."""
    try:
        resposta = supabase.table("batalhas").select("*").order("created_at", descending=True).execute()
        return resposta.data or []
    except Exception as erro:
        print(f"❌ Erro [listar_batalhas]: {erro}")
        return []


def criar_batalha(titulo, descricao, professor_id, quantidade_rodadas, tempo_por_rodada, criterios, regras, seguranca, prazo_iso) -> bool:
    """Registra uma nova rodada competitiva estruturada de batalhas no banco."""
    try:
        payload = {
            "titulo": str(titulo).strip(),
            "descricao": descricao,
            "criado_por": str(professor_id).strip(),
            "quantidade_rodadas": int(quantidade_rodadas),
            "tempo_por_rodada": int(tempo_por_rodada),
            "criterios_avaliacao": criterios,
            "regras_conduta": regras,
            "configuracoes_seguranca": seguranca,
            "prazo": prazo_iso,
            "finalizada": False
        }
        resposta = supabase.table("batalhas").insert(payload).execute()
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [criar_batalha]: {erro}")
        return False


def finalizar_batalha(batalha_id: str) -> bool:
    """Encerra administrativamente as submissões e o status de uma batalha específica."""
    if not str(batalha_id).strip():
        return False
    try:
        resposta = (
            supabase
            .table("batalhas")
            .update({"finalizada": True})
            .eq("id", str(batalha_id).strip())
            .execute()
        )
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"❌ Erro [finalizar_batalha]: {erro}")
        return False