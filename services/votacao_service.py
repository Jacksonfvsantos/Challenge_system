import streamlit as st
from database.conexao import supabase # ✅ CORRIGIDO: Puxando o cliente de escopo global com token service_role

def buscar_voto_usuario(usuario_id, desafio_id):
    """
    Busca se o usuário logado já votou em algum projeto para este desafio específico.
    """
    try:
        resultado = supabase.table("votos") \
            .select("*") \
            .eq("usuario_id", str(usuario_id)) \
            .eq("desafio_id", str(desafio_id)) \
            .execute()
        return resultado.data
    except Exception as e:
        print(f"Erro ao buscar voto: {e}")
        return []


def registrar_voto(desafio_id, aluno_id, usuario_id_logado):
    """
    Registra o voto do aluno logado no projeto do aluno autor dentro do desafio selecionado.
    """
    try:
        votos_existentes = buscar_voto_usuario(usuario_id_logado, desafio_id)
        
        if votos_existentes:
            return {
                "sucesso": False,
                "mensagem": "Você já registrou um voto para este desafio!"
            }
        
        dados_voto = {
            "usuario_id": str(usuario_id_logado),
            "desafio_id": str(desafio_id),
            "voto": str(aluno_id)
        }
        
        supabase.table("votos").insert(dados_voto).execute()
        
        return {
            "sucesso": True,
            "mensagem": "Voto computado com sucesso!"
        }
        
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro interno ao registrar o voto no banco: {str(e)}"
        }


def listar_votos():
    """
    Retorna a lista completa de votos registrados no sistema.
    """
    try:
        resultado = supabase.table("votos").select("*").execute()
        return resultado.data
    except Exception as e:
        print(f"Erro ao listar votos: {e}")
        return []