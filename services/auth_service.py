import hashlib
import re
from database.conexao import supabase
from services.notificacao_service import registrar_log_seguranca

def criptografar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

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

    verificar_usuario = supabase.table("usuarios").select("id").eq("email", email_sanitizado).execute()
    if verificar_usuario.data:
        registrar_log_seguranca(
            usuario_id=verificar_usuario.data[0]["id"],
            acao="LOGIN_FALHA_SENHA_INCORRETA",
            tabela_alvo="usuarios",
            detalhes={"email": email_sanitizado}
        )
    return None

def cadastrar_usuario(nome, email, tipo_usuario, senha):
    try:
        validar = senha_valida(senha)
        if validar != "ok":
            return validar

        email_sanitizado = str(email).strip().lower()

        verificar = (
            supabase
            .table("usuarios")
            .select("id")
            .eq("email", email_sanitizado)
            .execute()
        )

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