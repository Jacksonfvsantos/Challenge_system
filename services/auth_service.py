import hashlib
import re
from database.conexao import supabase

CHAVE_SECRETA_PROFESSOR = "PROFE-UNIJORGE-2026"
DOMINIO_ALUNO = "@unjorge.edu.br"
DOMINIO_PROFESSOR = "@unijorge.pro.br"

def criptografar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def e_mail_valido(email):
    padrao = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(padrao, email))

def senha_valida(senha):
    if len(senha) < 8:
        return "A senha deve ter no mínimo 8 caracteres"

    if not re.search(r"[A-Z]", senha):
        return "A senha deve conter pelo menos uma letra maiúscula"

    if not re.search(r"\d", senha):
        return "A senha deve conter pelo menos um número"

    return "ok"

def login_usuario(email, senha):
    email_sanitizado = str(email).strip().lower()
    
    if not e_mail_valido(email_sanitizado):
        return None

    resposta = (
        supabase
        .table("usuarios")
        .select("*")
        .eq("email", email_sanitizado)
        .eq("senha", criptografar_senha(senha))
        .execute()
    )

    if resposta.data:
        return resposta.data[0]

    return None

def cadastrar_usuario(nome, email, tipo_usuario, senha, codigo_ativacao=None):
    try:
        email_sanitizado = str(email).strip().lower()
        
        if not e_mail_valido(email_sanitizado):
            return "Formato de e-mail inválido"

        validar = senha_valida(senha)
        if validar != "ok":
            return validar

        tipo_sanitizado = str(tipo_usuario).strip().lower()

        if tipo_sanitizado == "aluno":
            if not email_sanitizado.endswith(DOMINIO_ALUNO):
                return f"Para o perfil Aluno, utilize o e-mail institucional contendo {DOMINIO_ALUNO}"

        elif tipo_sanitizado == "professor":
            if not email_sanitizado.endswith(DOMINIO_PROFESSOR):
                return f"Para o perfil Professor, utilize o e-mail institucional contendo {DOMINIO_PROFESSOR}"
            
            if not codigo_ativacao or codigo_ativacao.strip() != CHAVE_SECRETA_PROFESSOR:
                return "Código de ativação docente inválido ou ausente"

        verificar = (
            supabase
            .table("usuarios")
            .select("id")
            .eq("email", email_sanitizado)
            .execute()
        )

        if verificar.data:
            return "E-mail já cadastrado"

        supabase.table("usuarios").insert({
            "nome": nome.strip(),
            "email": email_sanitizado,
            "tipo_usuario": tipo_sanitizado,
            "senha": criptografar_senha(senha)
        }).execute()

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