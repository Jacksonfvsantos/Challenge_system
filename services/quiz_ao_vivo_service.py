import os
import uuid  # <-- Adicionado para validação permanente de chaves UUID
from typing import Any, Dict, List, Optional, Tuple

from supabase import Client, create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR-SUPABASE-URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR-SUPABASE-KEY")

banco: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================================
# Helper de Validação de UUID
# ==========================================
def _eh_uuid_valido(valor: Any) -> bool:
    """Verifica localmente se uma string está no formato UUID correto."""
    try:
        uuid.UUID(str(valor).strip())
        return True
    except ValueError:
        return False


# ==========================================
# Repository layer
# ==========================================
def _first_row(data: Any) -> Optional[Dict[str, Any]]:
    if isinstance(data, list):
        return data[0] if data else None
    return data if data else None


def repo_get_usuario(usuario_id: str) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(usuario_id):
        return None
    res = (
        banco.table("usuarios")
        .select("*")
        .eq("id", str(usuario_id).strip())
        .limit(1)
        .execute()
    )
    return _first_row(res.data)


def repo_insert_quiz(dados_quiz: Dict[str, Any]) -> Dict[str, Any]:
    res = banco.table("quizzes").insert(dados_quiz).execute()
    return _first_row(res.data) or {}


def repo_get_quiz(quiz_id: str) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(quiz_id):
        return None
    res = (
        banco.table("quizzes")
        .select("*")
        .eq("id", str(quiz_id).strip())
        .limit(1)
        .execute()
    )
    return _first_row(res.data)


def repo_update_quiz_status(quiz_id: str, status: str) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(quiz_id):
        return None
    res = (
        banco.table("quizzes")
        .update({"status": status})
        .eq("id", str(quiz_id).strip())
        .execute()
    )
    return _first_row(res.data)


def repo_update_pergunta_atual(
    quiz_id: str,
    pergunta_atual: int,
) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(quiz_id):
        return None
    res = (
        banco.table("quizzes")
        .update({"pergunta_atual": pergunta_atual})
        .eq("id", str(quiz_id).strip())
        .execute()
    )
    return _first_row(res.data)


def repo_update_quiz_inicio(quiz_id: str) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(quiz_id):
        return None
    res = (
        banco.table("quizzes")
        .update({"status": "iniciado", "pergunta_atual": 0})
        .eq("id", str(quiz_id).strip())
        .execute()
    )
    return _first_row(res.data)


def repo_insert_pergunta(dados_pergunta: Dict[str, Any]) -> Dict[str, Any]:
    # Ajustado para a tabela correta do novo Script SQL
    res = banco.table("perguntas_quiz").insert(dados_pergunta).execute()
    return _first_row(res.data) or {}


def repo_get_pergunta(pergunta_id: str) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(pergunta_id):
        return None
    res = (
        banco.table("perguntas_quiz")
        .select("*")
        .eq("id", str(pergunta_id).strip())
        .limit(1)
        .execute()
    )
    return _first_row(res.data)


def repo_get_perguntas_quizaovivo(quiz_id: str) -> List[Dict[str, Any]]:
    if not _eh_uuid_valido(quiz_id):
        return []
    res = (
        banco.table("perguntas_quiz")
        .select("*")
        .eq("quiz_id", str(quiz_id).strip())
        .order("ordem")  # Ordena pela coluna de ordenação sequencial do jogo
        .execute()
    )
    return res.data or []


def repo_insert_participacao_quizaovivo(
    dados_participacao: Dict[str, Any],
) -> Dict[str, Any]:
    # Ajustado para a tabela correta: participantes_quiz
    res = banco.table("participantes_quiz").insert(dados_participacao).execute()
    return _first_row(res.data) or {}


def repo_get_participacao_quizaovivo(
    participacao_id: str,
) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(participacao_id):
        return None
    res = (
        banco.table("participantes_quiz")
        .select("*")
        .eq("id", str(participacao_id).strip())
        .limit(1)
        .execute()
    )
    return _first_row(res.data)


def repo_get_participacao_por_aluno_quiz(
    aluno_id: str,
    quiz_id: str,
) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(aluno_id) or not _eh_uuid_valido(quiz_id):
        return None
    res = (
        banco.table("participantes_quiz")
        .select("*")
        .eq("usuario_id", str(aluno_id).strip())
        .eq("quiz_id", str(quiz_id).strip())
        .limit(1)
        .execute()
    )
    return _first_row(res.data)


def repo_update_pontuacao_participacao(
    participacao_id: str,
    nova_pontuacao: int,
) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(participacao_id):
        return None
    res = (
        banco.table("participantes_quiz")
        .update({"pontuacao": nova_pontuacao})
        .eq("id", str(participacao_id).strip())
        .execute()
    )
    return _first_row(res.data)


def repo_insert_resposta_quizaovivo(
    dados_resposta: Dict[str, Any],
) -> Dict[str, Any]:
    # Ajustado para a tabela correta: respostas_quiz
    res = banco.table("respostas_quiz").insert(dados_resposta).execute()
    return _first_row(res.data) or {}


def repo_get_resposta_por_participacao_pergunta(
    participacao_id: str,
    pergunta_id: str,
) -> Optional[Dict[str, Any]]:
    if not _eh_uuid_valido(participacao_id) or not _eh_uuid_valido(pergunta_id):
        return None
    res = (
        banco.table("respostas_quiz")
        .select("*")
        .eq("participante_id", str(participacao_id).strip())
        .eq("pergunta_id", str(pergunta_id).strip())
        .limit(1)
        .execute()
    )
    return _first_row(res.data)


def repo_get_ranking_quiz(quiz_id: str) -> List[Dict[str, Any]]:
    if not _eh_uuid_valido(quiz_id):
        return []
    res = (
        banco.table("participantes_quiz")
        .select("pontuacao, usuarios(nome)")
        .eq("quiz_id", str(quiz_id).strip())
        .order("pontuacao", desc=True)
        .execute()
    )
    return res.data or []


# ==========================================
# Service layer
# ==========================================
def _ok(dados: Any = None, mensagem: Optional[str] = None) -> Dict[str, Any]:
    resposta = {"sucesso": True}
    if dados is not None:
        resposta["dados"] = dados
    if mensagem:
        resposta["mensagem"] = message = mensagem
    return resposta


def _erro(mensagem: str) -> Dict[str, Any]:
    return {"sucesso": False, "mensagem": mensagem}


def _verificar_permissao_professor(usuario_id: str) -> Tuple[bool, str]:
    try:
        usuario = repo_get_usuario(usuario_id)
        if not usuario:
            return False, f"Usuario (ID: {usuario_id}) nao encontrado."

        tipo = str(usuario.get("tipo_usuario", "")).strip().lower()
        if tipo != "professor":
            return False, f"O tipo de usuario e '{usuario.get('tipo_usuario')}', mas exige-se 'professor'."

        return True, "Permitido"
    except Exception as exc:
        return False, f"Erro ao verificar usuario no Supabase: {exc}"


def _validar_professor_dono_quiz(
    quiz_id: str,
    professor_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    permitido, motivo = _verificar_permissao_professor(professor_id)
    if not permitido:
        return None, _erro(f"Acesso negado: {motivo}")

    quiz = repo_get_quiz(quiz_id)
    if not quiz:
        return None, _erro("Quiz nao encontrado.")

    if str(quiz.get("criado_por")) != str(professor_id).strip():
        return None, _erro("Este quiz pertence a outro professor.")

    return quiz, None


# --- Professor ---
def criar_quiz(titulo: str, professor_id: str) -> Dict[str, Any]:
    titulo = titulo.strip() if titulo else ""
    if len(titulo) < 3:
        return _erro("O titulo deve ter pelo menos 3 caracteres.")

    permitido, motivo = _verificar_permissao_professor(professor_id)
    if not permitido:
        return _erro(f"Acesso negado: {motivo}")

    novo_quiz = {
        "titulo": titulo,
        "criado_por": str(professor_id).strip(),
        "status": "criado",
        "pergunta_atual": 0,
    }

    try:
        return _ok(repo_insert_quiz(novo_quiz))
    except Exception as exc:
        return _erro(f"Erro interno no banco de dados: {exc}")


def adicionar_pergunta(
    quiz_id: str,
    professor_id: str,
    texto: str,
    alternativas: List[str],
    indice_correto: int,
) -> Dict[str, Any]:
    texto = texto.strip() if texto else ""
    alternativas_limpas = [alt.strip() for alt in alternativas if alt and alt.strip()]

    if len(texto) < 3:
        return _erro("O texto da pergunta deve ter pelo menos 3 caracteres.")

    if len(alternativas_limpas) < 2:
        return _erro("A pergunta deve ter pelo menos 2 alternativas.")

    if indice_correto < 0 or indice_correto >= len(alternativas_limpas):
        return _erro("Indice da alternativa correta e invalido.")

    try:
        _, erro = _validar_professor_dono_quiz(quiz_id, professor_id)
        if erro:
            return erro

        # Descobre a próxima ordem incremental das perguntas do quiz
        perguntas_existentes = repo_get_perguntas_quizaovivo(quiz_id)
        proxima_ordem = len(perguntas_existentes)

        nova_pergunta = {
            "quiz_id": str(quiz_id).strip(),
            "texto": texto,
            "alternativas": alternativas_limpas,
            "indice_correto": indice_correto,
            "ordem": proxima_ordem,
        }
        return _ok(repo_insert_pergunta(nova_pergunta))
    except Exception as exc:
        return _erro(f"Erro ao adicionar pergunta: {exc}")


def alterar_status_quiz(
    quiz_id: str,
    professor_id: str,
    novo_status: str,
) -> Dict[str, Any]:
    if novo_status not in {"iniciado", "finalizado"}:
        return _erro("Status invalido.")

    try:
        quiz, erro = _validar_professor_dono_quiz(quiz_id, professor_id)
        if erro:
            return erro

        if quiz and quiz.get("status") == "finalizado":
            return _erro("O quiz ja foi finalizado.")

        if novo_status == "iniciado":
            perguntas = repo_get_perguntas_quizaovivo(quiz_id)
            if not perguntas:
                return _erro("Nao e possivel iniciar um quiz sem perguntas.")
            dados = repo_update_quiz_inicio(quiz_id)
        else:
            dados = repo_update_quiz_status(quiz_id, novo_status)

        if not dados:
            return _erro("O status do quiz nao foi atualizado no Supabase.")

        return _ok(dados)
    except Exception as exc:
        return _erro(f"Erro ao alterar status: {exc}")


def avancar_pergunta(quiz_id: str, professor_id: str) -> Dict[str, Any]:
    try:
        quiz, erro = _validar_professor_dono_quiz(quiz_id, professor_id)
        if erro:
            return erro

        if quiz and quiz.get("status") != "iniciado":
            return _erro("Somente quizzes iniciados podem avancar pergunta.")

        perguntas = repo_get_perguntas_quizaovivo(quiz_id)
        if not perguntas:
            return _erro("Este quiz nao possui perguntas.")

        atual = quiz.get("pergunta_atual") if quiz else None
        if atual is None:
            atual = 0
        else:
            atual = int(atual)

        proxima = atual + 1
        if proxima >= len(perguntas):
            return _erro("Nao ha proxima pergunta.")

        dados = repo_update_pergunta_atual(quiz_id, proxima)
        if not dados:
            return _erro("A pergunta atual nao foi atualizada no Supabase.")

        return _ok(dados)
    except Exception as exc:
        return _erro(f"Erro ao avancar pergunta: {exc}")


# --- Aluno ---
def entrar_quiz(aluno_id: str, quiz_id: str) -> Dict[str, Any]:
    try:
        quiz = repo_get_quiz(quiz_id)
        if not quiz or quiz.get("status") != "iniciado":
            return _erro("Quiz indisponivel ou ja finalizado.")

        existente = repo_get_participacao_por_aluno_quiz(aluno_id, quiz_id)
        if existente:
            return _ok(existente, "Aluno ja ingressado neste quiz.")

        nova_participacao = {
            "quiz_id": str(quiz_id).strip(),
            "usuario_id": str(aluno_id).strip(),
            "pontuacao": 0,
        }
        return _ok(repo_insert_participacao_quizaovivo(nova_participacao))
    except Exception as exc:
        mensagem = str(exc)
        if "unique" in mensagem.lower():
            existente = repo_get_participacao_por_aluno_quiz(aluno_id, quiz_id)
            if existente:
                return _ok(existente, "Aluno ja ingressado neste quiz.")
        return _erro(f"Erro ao ingressar no quiz: {mensagem}")


def obter_participacao(participacao_id: str) -> Dict[str, Any]:
    try:
        participacao = repo_get_participacao_quizaovivo(participacao_id)
        if not participacao:
            return _erro("Participacao nao encontrada.")
        return _ok(participacao)
    except Exception as exc:
        return _erro(f"Erro ao obter participacao: {exc}")


def obter_pergunta_atual_quiz(quiz_id: str) -> Dict[str, Any]:
    try:
        quiz = repo_get_quiz(quiz_id)
        if not quiz:
            return _erro("Quiz nao encontrado.")

        perguntas = repo_get_perguntas_quizaovivo(quiz_id)
        atual = quiz.get("pergunta_atual")

        if quiz.get("status") != "iniciado":
            return _ok({"quiz": quiz, "pergunta": None, "indice": atual})

        if atual is None:
            return _erro("Quiz iniciado sem pergunta_atual definida.")

        indice = int(atual)
        if indice < 0 or indice >= len(perguntas):
            return _ok({"quiz": quiz, "pergunta": None, "indice": indice, "fim": True})

        pergunta = dict(perguntas[indice])
        pergunta.pop("indice_correto", None)

        return _ok(
            {
                "quiz": quiz,
                "pergunta": pergunta,
                "indice": indice,
                "total": len(perguntas),
                "fim": False,
            }
        )
    except Exception as exc:
        return _erro(f"Erro ao obter pergunta atual: {exc}")


def responder_pergunta(
    participacao_id: str,
    pergunta_id: str,
    indice_resposta: int,
) -> Dict[str, Any]:
    try:
        participacao = repo_get_participacao_quizaovivo(participacao_id)
        if not participacao:
            return _erro("Participacao invalida ou quiz ja finalizado.")

        pergunta = repo_get_pergunta(pergunta_id)
        if not pergunta:
            return _erro("Pergunta nao encontrada.")

        quiz = repo_get_quiz(participacao["quiz_id"])
        if not quiz or quiz.get("status") != "iniciado":
            return _erro("Quiz indisponivel para respostas.")

        perguntas = repo_get_perguntas_quizaovivo(participacao["quiz_id"])
        atual = quiz.get("pergunta_atual")
        if atual is None:
            return _erro("Quiz iniciado sem pergunta_atual definida.")

        indice_atual = int(atual)
        if indice_atual < 0 or indice_atual >= len(perguntas):
            return _erro("Nao ha pergunta atual para responder.")

        pergunta_atual = perguntas[indice_atual]
        if pergunta_atual.get("id") != pergunta_id:
            return _erro("Esta pergunta nao e a pergunta atual do quiz.")

        resposta_existente = repo_get_resposta_por_participacao_pergunta(
            participacao_id,
            pergunta_id,
        )
        if resposta_existente:
            return _erro("Voce ja respondeu esta pergunta.")

        alternativas = pergunta.get("alternativas") or []
        if indice_resposta < 0 or indice_resposta >= len(alternativas):
            return _erro("Indice da resposta e invalido.")

        correta = indice_resposta == pergunta.get("indice_correto")
        nova_resposta = {
            "participante_id": str(participacao_id).strip(),
            "pergunta_id": str(pergunta_id).strip(),
            "indice_resposta": indice_resposta,
            "correta": correta,
        }

        dados_resposta = repo_insert_resposta_quizaovivo(nova_resposta)
        pontuacao_atual = int(participacao.get("pontuacao") or 0)
        nova_pontuacao = pontuacao_atual + 10 if correta else pontuacao_atual

        if correta:
            repo_update_pontuacao_participacao(participacao_id, nova_pontuacao)

        return _ok(
            {
                "resposta_registrada": dados_resposta,
                "correta": correta,
                "feedback": "Resposta correta!" if correta else "Resposta incorreta.",
                "pontuacao": nova_pontuacao,
            }
        )
    except Exception as exc:
        if "unique" in str(exc).lower():
            return _erro("Voce ja respondeu esta pergunta.")
        return _erro(f"Erro ao registrar resposta: {exc}")


def obter_ranking(quiz_id: str) -> Dict[str, Any]:
    try:
        return _ok(repo_get_ranking_quiz(quiz_id))
    except Exception as exc:
        return _erro(f"Erro ao obter ranking: {exc}")


def obter_perguntas_quizaovivo(quiz_id: str) -> Dict[str, Any]:
    try:
        perguntas = repo_get_perguntas_quizaovivo(quiz_id)
        perguntas_sem_gabarito = []
        for pergunta in perguntas:
            segura = dict(pergunta)
            segura.pop("indice_correto", None)
            perguntas_sem_gabarito.append(segura)
        return _ok(perguntas_sem_gabarito)
    except Exception as exc:
        return _erro(f"Erro ao obter perguntas: {exc}")