from database.conexao import supabase

<<<<<<< HEAD
def buscar_professor_por_email(email):
    try:
        resposta = (
            supabase
            .table("usuarios")
            .select("*")
            .eq("email", email)
            .eq("tipo_usuario", "professor")
            .execute()
        )
        if resposta.data:
            return resposta.data[0]
        
        resposta = (
            supabase
            .table("usuarios")
            .select("*")
            .eq("email", email)
            .execute()
        )
        if resposta.data:
            return resposta.data[0]
        return None
    except Exception:
        return None

def buscar_ou_criar_disciplina(nome):
    if not nome:
        nome = "Geral"
    nome_limpo = str(nome).strip()
    try:
        buscar = (
            supabase
            .table("disciplinas")
            .select("*")
            .eq("nome", nome_limpo)
            .execute()
        )
        if buscar.data:
            return buscar.data[0]
        
        criar = (
            supabase
            .table("disciplinas")
            .insert({"nome": nome_limpo})
            .execute()
        )
        return criar.data[0]
    except Exception:
        # Fallback de segurança para não travar o cadastro de questões
        return {"id": None}

def criar_pergunta(dados):
    """Insere a questão e suas alternativas associadas com tratamento de erros robusto."""
    try:
        professor = buscar_professor_por_email(dados["email_professor"])
        if not professor:
            return {"sucesso": False, "mensagem": "Perfil de professor autor não localizado."}

        disciplina = buscar_ou_criar_disciplina(dados["disciplina"])

        # 1. Insere a questão na tabela principal
        payload_questao = {
            "professor_id":  professor["id"],
=======

def buscar_professor_por_email(email):
    # Busca na tabela usuarios (nao existe tabela professores)
    resposta = (
        supabase
        .table("usuarios")
        .select("*")
        .eq("email", email)
        .eq("tipo_usuario", "professor")
        .execute()
    )
    if resposta.data:
        return resposta.data[0]
    # Tenta também admin
    resposta = (
        supabase
        .table("usuarios")
        .select("*")
        .eq("email", email)
        .execute()
    )
    if resposta.data:
        return resposta.data[0]
    return None


def buscar_ou_criar_disciplina(nome):
    buscar = (
        supabase
        .table("disciplinas")
        .select("*")
        .eq("nome", nome)
        .execute()
    )
    if buscar.data:
        return buscar.data[0]
    criar = (
        supabase
        .table("disciplinas")
        .insert({"nome": nome})
        .execute()
    )
    return criar.data[0]


def criar_pergunta(dados):
    professor = buscar_professor_por_email(dados["email_professor"])
    if not professor:
        return None

    disciplina = buscar_ou_criar_disciplina(dados["disciplina"])

    questao = (
        supabase
        .table("questoes")
        .insert({
            "professor_id":  professor["id"],
            "disciplina_id": disciplina["id"],
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
            "tipo":          "multipla_escolha",
            "nivel":         dados["nivel"],
            "enunciado":     dados["enunciado"],
            "pontos":        1
<<<<<<< HEAD
        }
        
        if disciplina.get("id"):
            payload_questao["disciplina_id"] = disciplina["id"]

        questao = (
            supabase
            .table("questoes")
            .insert(payload_questao)
            .execute()
        )

        if not questao.data:
            return {"sucesso": False, "mensagem": "Falha operacional ao registrar a questão."}

        questao_id = questao.data[0]["id"]

        # 2. Insere as 5 alternativas vinculadas
        alternativas = [
            dados["alternativa_a"],
            dados["alternativa_b"],
            dados["alternativa_c"],
            dados["alternativa_d"],
            dados["alternativa_e"]
        ]
        letras = ["A", "B", "C", "D", "E"]

        for i in range(5):
            if alternativas[i]:  # Apenas grava se a alternativa não estiver em branco
                supabase.table("alternativas").insert({
                    "questao_id": questao_id,
                    "texto":      alternativas[i].strip(),
                    "correta":    (letras[i] == dados["resposta_correta"]),
                    "ordem":      i + 1
                }).execute()

        return {"sucesso": True, "mensagem": "Questão e alternativas salvas com sucesso!"}

    except Exception as e:
        if "42501" in str(e):
            return {"sucesso": False, "mensagem": "Acesso negado pelo servidor: Segurança RLS ativa na tabela de Questões."}
        return {"sucesso": False, "mensagem": f"Erro de consistência com o banco: {str(e)}"}

def listar_mini_provas():
    try:
        resposta = supabase.table("mini_provas").select("*").execute()
        return resposta.data or []
    except Exception:
        return []

def listar_perguntas():
    """Busca com segurança prevenindo travamentos de inicialização da tela."""
    try:
        resposta = supabase.table("questoes").select("*").execute()
        return resposta.data or []
    except Exception:
        return []

def excluir_pergunta(id_pergunta):
    try:
        # Remove as alternativas filhas primeiro devido à restrição de chave estrangeira (FK)
        supabase.table("alternativas").delete().eq("questao_id", id_pergunta).execute()
        supabase.table("questoes").delete().eq("id", id_pergunta).execute()
        return True
    except Exception:
        return False

# ... (as demais funções de mini_prova permanecem idênticas abaixo)
=======
        })
        .execute()
    )

    questao_id = questao.data[0]["id"]

    alternativas = [
        dados["alternativa_a"],
        dados["alternativa_b"],
        dados["alternativa_c"],
        dados["alternativa_d"],
        dados["alternativa_e"]
    ]
    letras = ["A", "B", "C", "D", "E"]

    for i in range(5):
        supabase.table("alternativas").insert({
            "questao_id": questao_id,
            "texto":      alternativas[i],
            "correta":    (letras[i] == dados["resposta_correta"]),
            "ordem":      i + 1
        }).execute()


def criar_mini_prova(dados):
    professor = buscar_professor_por_email(dados["email_professor"])
    if not professor:
        return None

    payload = {
        "professor_id": professor["id"],
        "titulo":       dados["titulo"],
        "descricao":    dados.get("assunto", ""),
    }

    # Adiciona campos opcionais se a tabela suportar
    campos_opcionais = {
        "qtde_questoes":   dados.get("quantidade_total"),
        "duracao_minutos": dados.get("tempo_minutos"),
        "status":          "rascunho",
    }
    for campo, valor in campos_opcionais.items():
        if valor is not None:
            payload[campo] = valor

    try:
        disciplina = buscar_ou_criar_disciplina(dados["disciplina"])
        payload["disciplina_id"] = disciplina["id"]
    except Exception:
        pass

    resposta = (
        supabase
        .table("mini_provas")
        .insert(payload)
        .execute()
    )
    return resposta.data


def listar_mini_provas():
    resposta = (
        supabase
        .table("mini_provas")
        .select("*")
        .execute()
    )
    return resposta.data or []


def listar_perguntas():
    resposta = (
        supabase
        .table("questoes")
        .select("*")
        .execute()
    )
    return resposta.data or []


def buscar_pergunta(id_pergunta):
    resposta = (
        supabase
        .table("questoes")
        .select("*")
        .eq("id", id_pergunta)
        .execute()
    )
    if resposta.data:
        return resposta.data[0]
    return None


def atualizar_pergunta(id_pergunta, dados):
    supabase.table("questoes").update({
        "enunciado": dados["enunciado"],
        "nivel":     dados["nivel"]
    }).eq("id", id_pergunta).execute()


def excluir_pergunta(id_pergunta):
    supabase.table("questoes").delete().eq("id", id_pergunta).execute()


def buscar_mini_prova(id_mini_prova):
    resposta = (
        supabase
        .table("mini_provas")
        .select("*")
        .eq("id", id_mini_prova)
        .execute()
    )
    if resposta.data:
        return resposta.data[0]
    return None


def atualizar_mini_prova(id_mini_prova, dados):
    payload = {}
    for campo in ["titulo", "descricao", "qtde_questoes", "duracao_minutos"]:
        if campo in dados:
            payload[campo] = dados[campo]
    if payload:
        supabase.table("mini_provas").update(payload).eq("id", id_mini_prova).execute()


def excluir_mini_prova(id_mini_prova):
    supabase.table("mini_provas").delete().eq("id", id_mini_prova).execute()
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
