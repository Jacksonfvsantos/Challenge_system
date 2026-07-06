import hashlib
import re
from database.conexao import supabase
from services.notificacao_service import registrar_log_seguranca

def eh_email_valido(email):
    """Verifica se a estrutura do e-mail é válida matematicamente."""
    padrao = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(padrao, email) is not None

def criptografar_senha(senha):
    """Gera o hash SHA-256 da senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def senha_valida(senha):
    """Valida requisitos mínimos de segurança para senhas."""
    if len(senha) < 8:
        return "A senha deve ter no mínimo 8 caracteres"
    if not re.search(r"[A-Z]", senha):
        return "A senha deve conter pelo menos uma letra maiúscula"
    if not re.search(r"\d", senha):
        return "A senha deve conter pelo menos um número"
    return "ok"

def definir_tipo_usuario_por_email(email):
    """
    Atribui o perfil do usuário baseado no domínio institucional.
    Adapte a lista de domínios conforme a necessidade da sua instituição.
    """
    email_sanitizado = str(email).strip().lower()
    # Exemplo: domínios de professor
    if email_sanitizado.endswith("@unijorge.edu.br"): 
        return "professor"
    # Padrão para alunos
    return "aluno"

def login_usuario(email, senha):
    email_sanitizado = str(email).strip().lower()
    
    resposta = (
        supabase
        .table("usuarios")
        .select("*")
        .eq("email", email_sanitizado)
        .eq("senha", criptografar_senha(senha))
        .execute()
    )

    if resposta.data:
        usuario = resposta.data[0]
        registrar_log_seguranca(
            usuario_id=usuario["id"],
            acao="LOGIN_SUCESSO",
            tabela_alvo="usuarios",
            detalhes={"email": email_sanitizado}
        )
        return usuario

    # Log de falha caso o e-mail exista mas a senha esteja incorreta
    verificar_usuario = supabase.table("usuarios").select("id").eq("email", email_sanitizado).execute()
    if verificar_usuario.data:
        registrar_log_seguranca(
            usuario_id=verificar_usuario.data[0]["id"],
            acao="LOGIN_FALHA_SENHA_INCORRETA",
            tabela_alvo="usuarios",
            detalhes={"email": email_sanitizado}
        )
    return None

def cadastrar_usuario(nome, email, senha):
    """
    Cadastra o usuário automaticamente com o perfil padrão de 'aluno'.
    """
    try:
        email_sanitizado = str(email).strip().lower()
        
        if not eh_email_valido(email_sanitizado):
            return "Formato de e-mail inválido."
            
        provedores_bloqueados = ["yopmail.com", "tempmail.com", "mailinator.com"]
        dominio = email_sanitizado.split("@")[1]
        if dominio in provedores_bloqueados:
            return "E-mails temporários não são permitidos."

        validar = senha_valida(senha)
        if validar != "ok":
            return validar

        # 🚨 MUDANÇA AQUI: Todo mundo nasce como aluno
        tipo_usuario = "aluno" 

        verificar = supabase.table("usuarios").select("id").eq("email", email_sanitizado).execute()
        if verificar.data:
            return "E-mail já cadastrado"

        res_cadastro = supabase.table("usuarios").insert({
            "nome": nome.strip(),
            "email": email_sanitizado,
            "tipo_usuario": tipo_usuario,
            "senha": criptografar_senha(senha)
        }).execute()

        if res_cadastro.data:
            novo_usuario_id = res_cadastro.data[0]["id"]
            registrar_log_seguranca(
                usuario_id=novo_usuario_id,
                acao="CADASTRO_NOVO_USUARIO",
                tabela_alvo="usuarios",
                detalhes={"email": email_sanitizado, "tipo_usuario": tipo_usuario}
            )

        return "ok"

    except Exception as erro:
        return f"Erro ao cadastrar usuário: {erro}"

def excluir_conta_usuario(usuario_id: str) -> bool:
    try:
        resposta = (
            supabase
            .table("usuarios")
            .delete()
            .eq("id", str(usuario_id).strip())
            .execute()
        )
        return len(resposta.data) > 0
    except Exception as erro:
        print(f"Erro ao excluir conta: {erro}")
        return False
    
def alterar_privilegio_usuario(usuario_alvo_id: str, novo_tipo: str) -> bool:
    """Função exclusiva para o ADM promover ou rebaixar usuários."""
    try:
        if novo_tipo not in ["aluno", "professor", "admin"]:
            return False
            
        resposta = supabase.table("usuarios").update({
            "tipo_usuario": novo_tipo
        }).eq("id", str(usuario_alvo_id).strip()).execute()
        
        return len(resposta.data) > 0
    except Exception as e:
        print(f"Erro ao alterar privilégio: {e}")
        return False
    
def listar_usuarios():
    """Retorna todos os usuários cadastrados no sistema."""
    try:
        res = supabase.table("usuarios").select("id, nome, email, tipo_usuario").order("nome").execute()
        return res.data or []
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return []