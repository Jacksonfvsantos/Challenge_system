import streamlit as st
import random
from database.conexao import supabase

# ============================================================================
# 1. FUNÇÕES PARA QUESTÕES (BANCO DE PERGUNTAS)
# ============================================================================

def criar_pergunta(dados: dict) -> dict:
    """
    Cadastra uma nova pergunta de múltipla escolha vinculada a uma disciplina e assunto.
    """
    try:
        payload = {
            "email_professor": dados.get("email_professor"),
            "disciplina": str(dados.get("disciplina")).strip(),
            "assunto": str(dados.get("assunto")).strip(),
            "enunciado": str(dados.get("enunciado")).strip(),
            "nivel": str(dados.get("nivel", "facil")).strip().lower(),
            "alternativa_a": str(dados.get("alternativa_a")).strip(),
            "alternativa_b": str(dados.get("alternativa_b")).strip(),
            "alternativa_c": str(dados.get("alternativa_c")).strip(),
            "alternativa_d": str(dados.get("alternativa_d")).strip(),
            "alternativa_e": str(dados.get("alternativa_e")).strip(),
            "resposta_correta": str(dados.get("resposta_correta")).strip().upper()
        }
        supabase.table("perguntas_mini_provas").insert(payload).execute()
        return {"sucesso": True, "mensagem": "Questão cadastrada com sucesso!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao cadastrar questão: {str(e)}"}

def listar_perguntas():
    """
    Retorna todas as perguntas cadastradas no repositório.
    """
    try:
        res = supabase.table("perguntas_mini_provas").select("*").order("created_at", descending=True).execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Erro [listar_perguntas]: {e}")
        return []

def excluir_pergunta(id_pergunta: str) -> bool:
    """
    Remove uma questão específica do banco de dados.
    """
    try:
        supabase.table("perguntas_mini_provas").delete().eq("id", id_pergunta).execute()
        return True
    except Exception as e:
        print(f"❌ Erro [excluir_pergunta]: {e}")
        return False

# ============================================================================
# 2. FUNÇÕES PARA ESTRUTURAÇÃO DAS MINI PROVAS
# ============================================================================

def criar_mini_prova(dados: dict) -> dict:
    """
    Cria a definição de uma mini prova com quantidades de questões divididas por dificuldade.
    """
    try:
        payload = {
            "email_professor": dados.get("email_professor"),
            "titulo": str(dados.get("titulo")).strip(),
            "disciplina": str(dados.get("disciplina")).strip(),
            "assunto": str(dados.get("assunto")).strip(),
            "qtde_questoes": int(dados.get("quantidade_total", 5)),
            "qtd_faceis": int(dados.get("quantidade_faceis", 0)),
            "qtd_medias": int(dados.get("quantidade_medias", 0)),
            "qtd_dificeis": int(dados.get("quantidade_dificeis", 0)),
            "duracao_minutos": int(dados.get("tempo_minutos", 5)),
            "pontos_maximos": float(dados.get("pontos", 1.0)),
            "status": "ativo"
        }
        supabase.table("mini_provas").insert(payload).execute()
        return {"sucesso": True, "mensagem": "Mini prova configurada com sucesso!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao criar mini prova: {e}"}

def listar_mini_provas():
    """
    Lista todas as mini provas configuradas no sistema.
    """
    try:
        res_real = supabase.table("mini_provas").select("*").order("created_at", descending=True).execute()
        return res_real.data or []
    except Exception:
        return []

def buscar_mini_prova(id_prova):
    try:
        res = supabase.table("mini_provas").select("*").eq("id", id_prova).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

# ============================================================================
# 🎯 3. MOTOR DE EXECUÇÃO AUTOMATIZADA DA PROVA (SORTEIO SEGURO)
# ============================================================================

def gerar_caderno_questoes_dinamico(prova_id):
    """
    Monta uma mini prova personalizada para o aluno sorteando as questões
    do banco de dados com base nas quantidades de dificuldade exigidas.
    """
    try:
        res_prova = supabase.table("mini_provas").select("*").eq("id", prova_id).execute()
        if not res_prova.data:
            return []
            
        p = res_prova.data[0]

        # Busca todas as perguntas da disciplina/assunto correspondente
        query = supabase.table("perguntas_mini_provas").select("*")\
            .eq("disciplina", p["disciplina"]).eq("assunto", p["assunto"]).execute()
        
        todas_questoes = query.data or []
        
        faceis = [q for q in todas_questoes if str(q["nivel"]).lower() == "facil"]
        medias = [q for q in todas_questoes if str(q["nivel"]).lower() in ("medias", "intermediario", "medio", "intermediária")]
        dificeis = [q for q in todas_questoes if str(q["nivel"]).lower() == "dificil"]

        # Sorteia aleatoriamente respeitando a configuração da prova (Evita cola)
        sorteadas = []
        sorteadas.extend(random.sample(faceis, min(len(faceis), p.get("qtd_faceis", 0))))
        sorteadas.extend(random.sample(medias, min(len(medias), p.get("qtd_medias", 0))))
        sorteadas.extend(random.sample(dificeis, min(len(dificeis), p.get("qtd_dificeis", 0))))

        # Se o banco não tiver questões suficientes daquela dificuldade, completa com o que houver
        if len(sorteadas) < p["qtde_questoes"]:
            restantes = [q for q in todas_questoes if q not in sorteadas]
            falta = p["qtde_questoes"] - len(sorteadas)
            sorteadas.extend(random.sample(restantes, min(len(restantes), falta)))

        return sorteadas[:p["qtde_questoes"]]
    except Exception as e:
        print(f"❌ Erro ao sortear caderno de questões: {e}")
        return []

def computar_resultado_avaliacao(aluno_id, prova_id, respostas_aluno: dict, caderno_questoes: list) -> dict:
    """
    Processa o gabarito oficial em tempo real, calcula a nota proporcional e salva o log.
    """
    try:
        res_prova = buscar_mini_prova(prova_id)
        if not res_prova: 
            return {"sucesso": False, "mensagem": "Prova inválida."}

        total_questoes = len(caderno_questoes)
        acertos = 0

        # Validação do gabarito das alternativas submetidas
        for idx, questao in enumerate(caderno_questoes):
            resp_aluno = respostas_aluno.get(idx)
            if resp_aluno and str(resp_aluno).strip().upper() == str(questao["resposta_correta"]).strip().upper():
                acertos += 1

        # Cálculo da Nota de 0 a 10 e Pontuação proporcional (XP)
        nota = (acertos / total_questoes) * 10 if total_questoes > 0 else 0
        pontos_ganhos = (acertos / total_questoes) * res_prova["pontos_maximos"] if total_questoes > 0 else 0

        payload_historico = {
            "usuario_id": aluno_id,
            "mini_prova_id": prova_id,
            "nota": round(nota, 1),
            "pontos_obtidos": round(pontos_ganhos, 2),
            "total_questoes": total_questoes,
            "total_acertos": acertos
        }

        # Salva o log definitivo de desempenho do estudante
        supabase.table("historico_mini_provas").insert(payload_historico).execute()

        return {
            "sucesso": True,
            "nota": round(nota, 1),
            "pontos": round(pontos_ganhos, 2),
            "acertos": f"{acertos}/{total_questoes}"
        }
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro crítico na correção automática: {e}"}