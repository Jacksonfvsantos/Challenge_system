import streamlit as st
import random
from database.conexao import supabase

# ============================================================================
# 1. FUNÇÕES PARA QUESTÕES (BANCO DE PERGUNTAS RELACIONAL)
# ============================================================================

def criar_pergunta(dados: dict) -> dict:
    """
    Cadastra uma nova pergunta associando-a à tabela relacional de questões e alternativas.
    """
    try:
        # 1. Insere a questão atrelada à prova
        payload_questao = {
            "mini_prova_id": dados.get("mini_prova_id"),
            "enunciado": str(dados.get("enunciado")).strip()
        }
        res_q = supabase.table("questoes").insert(payload_questao).execute()
        if not res_q.data:
            return {"sucesso": False, "mensagem": "Erro ao gerar ID da questão."}
        
        questao_id = res_q.data[0]["id"]
        
        # 2. Prepara o lote de alternativas seguindo o DDL original
        alternativas_lote = []
        opcoes = ['A', 'B', 'C', 'D', 'E']
        gabarito = str(dados.get("resposta_correta")).strip().upper()
        
        for idx, letra in enumerate(opcoes):
            campo_texto = dados.get(f"alternativa_{letra.lower()}")
            if campo_texto:
                alternativas_lote.append({
                    "questao_id": questao_id,
                    "texto": str(campo_texto).strip(),
                    "ordem": idx + 1,
                    "correta": (letra == gabarito)
                })
                
        if alternativas_lote:
            supabase.table("alternativas").insert(alternativas_lote).execute()
            
        return {"sucesso": True, "mensagem": "Questão e alternativas salvas com sucesso!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao cadastrar questão relacional: {str(e)}"}

def listar_mini_provas():
    """
    Lista todas as mini provas configuradas no sistema de acordo com o DDL real.
    """
    try:
        res_real = supabase.table("mini_provas").select("*").order("data_criacao", desc=True).execute()
        return res_real.data or []
    except Exception as e:
        print(f"❌ Erro [listar_mini_provas]: {e}")
        return []

def buscar_mini_prova(id_prova):
    """
    Busca os metadados de uma única prova.
    """
    try:
        res = supabase.table("mini_provas").select("*").eq("id", id_prova).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

# ============================================================================
# 🎯 2. MOTOR DE MAPEAMENTO E CORREÇÃO ADAPTADO AO SCHEMA REAL
# ============================================================================

def gerar_caderno_questoes_dinamico(prova_id):
    """
    Busca as questões vinculadas à mini prova e injeta suas alternativas correspondentes.
    """
    try:
        # Busca todas as questões da prova
        res_q = supabase.table("questoes").select("*").eq("mini_prova_id", prova_id).execute()
        questoes = res_q.data or []
        
        if not questoes:
            return []
            
        caderno_completo = []
        
        # Para cada questão, busca o seu respectivo bloco de alternativas no banco
        for q in questoes:
            res_alt = supabase.table("alternativas").select("*").eq("questao_id", q["id"]).order("ordem").execute()
            lista_alt = res_alt.data or []
            
            # Monta um dicionário amigável para a renderização na tela 'responder.py'
            item_caderno = {
                "id": q["id"],
                "enunciado": q["enunciado"],
                "alternativas": [alt["texto"] for alt in lista_alt],
                "gabarito_texto": next((alt["texto"] for alt in lista_alt if alt["correta"]), None)
            }
            caderno_completo.append(item_caderno)
            
        # Sorteia a ordem das questões para evitar cola (Mantendo a quantidade definida)
        random.shuffle(caderno_completo)
        return caderno_completo
        
    except Exception as e:
        print(f"❌ Erro ao gerar caderno relacional: {e}")
        return []

def computar_resultado_avaliacao(aluno_id, prova_id, respostas_aluno: dict, caderno_questoes: list) -> dict:
    """
    Valida as respostas do caderno relacional, computa a nota e salva na tabela 'historico_provas'.
    """
    try:
        total_questoes = len(caderno_questoes)
        acertos = 0

        # Confere a alternativa marcada com o texto marcado como correto no lote do caderno
        for idx, q_caderno in enumerate(caderno_questoes):
            resp_marcada = respostas_aluno.get(idx)
            if resp_marcada and str(resp_marcada).strip() == str(q_caderno["gabarito_texto"]).strip():
                acertos += 1

        # Cálculo de notas baseado no padrão acadêmico
        nota = (acertos / total_questoes) * 10 if total_questoes > 0 else 0
        
        # Define 1.0 ponto de XP máximo por prova, fracionado pelo aproveitamento
        pontos_ganhos = (acertos / total_questoes) * 1.0 if total_questoes > 0 else 0

        # Payload casado perfeitamente com as colunas da tabela 'public.historico_provas'
        payload_historico = {
            "usuario_id": aluno_id,
            "mini_prova_id": prova_id,
            "nota": round(float(nota), 2),
            "pontuacao": round(float(pontos_ganhos), 2),
            "acertos": f"{acertos}/{total_questoes}"
        }

        # Insere o log definitivo de execução
        supabase.table("historico_provas").insert(payload_historico).execute()

        return {
            "sucesso": True,
            "nota": round(nota, 1),
            "pontos": round(pontos_ganhos, 2),
            "acertos": f"{acertos}/{total_questoes}"
        }
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro crítico na correção automática: {e}"}