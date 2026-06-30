import random
from database.conexao import supabase

def criar_pergunta(dados: dict) -> dict:
    try:
        payload_questao = {
            "mini_prova_id": dados.get("mini_prova_id"),
            "enunciado": str(dados.get("enunciado")).strip()
        }
        res_q = supabase.table("questoes").insert(payload_questao).execute()
        if not res_q.data:
            return {"sucesso": False, "mensagem": "Erro ao gerar ID da questão."}
        
        questao_id = res_q.data[0]["id"]
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
    try:
        res_real = supabase.table("mini_provas").select("*").order("data_criacao", desc=True).execute()
        return res_real.data or []
    except Exception as e:
        print(f"❌ Erro [listar_mini_provas]: {e}")
        return []

def buscar_mini_prova(id_prova):
    try:
        res = supabase.table("mini_provas").select("*").eq("id", id_prova).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def gerar_caderno_questoes_dinamico(prova_id):
    try:
        res_q = supabase.table("questoes").select("*").eq("mini_prova_id", prova_id).execute()
        questoes = res_q.data or []
        if not questoes:
            return []
            
        caderno_completo = []
        for q in questoes:
            res_alt = supabase.table("alternativas").select("*").eq("questao_id", q["id"]).order("ordem").execute()
            lista_alt = res_alt.data or []
            
            item_caderno = {
                "id": q["id"],
                "enunciado": q["enunciado"],
                "alternativas": [alt["texto"] for alt in lista_alt],
                "gabarito_texto": next((alt["texto"] for alt in lista_alt if alt["correta"]), None)
            }
            caderno_completo.append(item_caderno)
            
        random.shuffle(caderno_completo)
        return caderno_completo
    except Exception as e:
        print(f"❌ Erro ao gerar caderno relacional: {e}")
        return []

def computar_resultado_avaliacao(aluno_id, prova_id, respostas_aluno: dict, caderno_questoes: list) -> dict:
    try:
        total_questoes = len(caderno_questoes)
        acertos = 0

        for idx, q_caderno in enumerate(caderno_questoes):
            resp_marcada = respostas_aluno.get(idx)
            if resp_marcada and str(resp_marcada).strip() == str(q_caderno["gabarito_texto"]).strip():
                acertos += 1

        nota = (acertos / total_questoes) * 10 if total_questoes > 0 else 0
        pontos_ganhos = (acertos / total_questoes) * 1.0 if total_questoes > 0 else 0

        payload_historico = {
            "usuario_id": aluno_id,
            "mini_prova_id": prova_id,
            "nota": round(float(nota), 2),
            "pontuacao": round(float(pontos_ganhos), 2),
            "acertos": f"{acertos}/{total_questoes}"
        }

        supabase.table("historico_provas").insert(payload_historico).execute()
        return {
            "sucesso": True,
            "nota": round(nota, 1),
            "pontos": round(pontos_ganhos, 2),
            "acertos": f"{acertos}/{total_questoes}"
        }
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro crítico na correção automática: {e}"}

# =========================================================================
# NOVAS FUNÇÕES: ISOLAMENTO DE BANCO DE DADOS (SEPARAÇÃO DE CAMADAS)
# =========================================================================

def criar_escopo_mini_prova(titulo, duracao_minutos, criado_por, data_expiracao):
    try:
        payload = {
            "titulo": titulo.strip(),
            "quantidade_questoes": 0,
            "duracao_minutos": int(duracao_minutos),
            "criado_por": criado_por,
            "data_expiracao": data_expiracao
        }
        res = supabase.table("mini_provas").insert(payload).execute()
        return {"sucesso": True, "dados": res.data} if res.data else {"sucesso": False, "mensagem": "Falha ao gravar no banco."}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def listar_provas_professor(usuario_id):
    try:
        res = supabase.table("mini_provas").select("id, titulo").eq("criado_por", usuario_id).execute()
        return res.data or []
    except Exception:
        return []

def salvar_questao_com_alternativas(prova_id, enunciado, alternativas, correta_letra):
    try:
        res_q = supabase.table("questoes").insert({"mini_prova_id": prova_id, "enunciado": enunciado}).execute()
        if not res_q.data: 
            return {"sucesso": False, "mensagem": "Erro ao criar questão"}
        
        q_id = res_q.data[0]["id"]
        lote = []
        letras = ["A", "B", "C", "D"]
        for i, alt in enumerate(alternativas):
            lote.append({"questao_id": q_id, "texto": alt, "correta": (correta_letra == letras[i])})
            
        supabase.table("alternativas").insert(lote).execute()
        return {"sucesso": True, "mensagem": "Questão e alternativas salvas com sucesso!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}

def salvar_questoes_lote_ia(prova_id, questoes_geradas):
    try:
        if not questoes_geradas:
            return {"sucesso": False, "mensagem": "Nenhuma questão gerada para salvar."}
            
        for q in questoes_geradas:
            res_q = supabase.table("questoes").insert({
                "mini_prova_id": prova_id, 
                "enunciado": q["enunciado"]
            }).execute()
            
            if res_q.data:
                q_id = res_q.data[0]["id"]
                lote = [{"questao_id": q_id, "texto": alt, "correta": (i == q["correta_idx"])} 
                        for i, alt in enumerate(q["alternativas"])]
                supabase.table("alternativas").insert(lote).execute()
                
        return {"sucesso": True, "mensagem": f"{len(questoes_geradas)} questões injetadas!"}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}