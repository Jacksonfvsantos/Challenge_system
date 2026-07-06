import streamlit as st
from database.conexao import supabase

def listar_desafios():
    try:
        resultado = (
            supabase.table("desafios")
            .select("*")
            .order("criado_em", descending=True)
            .execute()
        )
        return resultado.data
    except Exception:
        try:
            resultado = supabase.table("desafios").select("*").execute()
            return resultado.data
        except Exception as erro_critico:
            print(f"Erro crítico ao listar desafios: {erro_critico}")
            return []

def criar_desafio(titulo, descricao, criador_id, data_limite, nivel):
    try:
        dados = {
            "titulo": str(titulo),
            "descricao": str(descricao),
            "criado_por": str(criador_id),
            "nivel_dificuldade": str(nivel),
            "data_limite": str(data_limite)
        }
        res = supabase.table("desafios").insert(dados).execute()
        return {"sucesso": True, "dados": res.data}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro: {str(e)}"}