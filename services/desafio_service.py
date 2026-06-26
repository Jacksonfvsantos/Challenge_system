import streamlit as st
from database.conexao import supabase # ✅ CORRIGIDO: Removidos imports redundantes para evitar falha de RLS

def listar_desafios():
    """
    Retorna a lista de todos os desafios cadastrados.
    Usa a coluna correta criado_em mapeada do PostgreSQL.
    """
    try:
        resultado = supabase.table("desafios") \
            .select("*") \
            .order("criado_em", descending=True) \
            .execute()
        return resultado.data
    except Exception:
        try:
            resultado = supabase.table("desafios").select("*").execute()
            return resultado.data
        except Exception as erro_critico:
            print(f"Erro crítico ao listar desafios: {erro_critico}")
            return []


def criar_desafio(titulo, descricao, criador_id, data_limite=None, nivel_dificuldade="Medio"):
    try:
        dados = {
            "titulo": str(titulo),
            "descricao": str(descricao),
            "criador_id": str(criador_id).strip(),
            "nivel_dificuldade": str(nivel_dificuldade)
        }
        if data_limite:
            dados["data_limite"] = str(data_limite)
            
        resultado = supabase.table("desafios").insert(dados).execute()
        return {"sucesso": True, "dados": resultado.data}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao criar desafio: {str(e)}"}