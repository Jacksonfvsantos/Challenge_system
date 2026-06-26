import streamlit as st
import time
from database.conexao import supabase

def buscar_dados_quiz(quiz_id):
    try:
        # Busca o quiz e a pergunta que está marcada como ativa atualmente
        res = supabase.table("quizzes").select("*").eq("id", quiz_id).single().execute()
        return res.data
    except Exception:
        return None

def buscar_perguntas_do_quiz(quiz_id):
    try:
        res = supabase.table("perguntas_quiz").select("*").eq("quiz_id", quiz_id).order("ordem").execute()
        return res.data or []
    except Exception:
        return []

def buscar_alternativas(pergunta_id):
    try:
        res = supabase.table("alternativas_quiz").select("*").eq("pergunta_id", pergunta_id).order("ordem").execute()
        return res.data or []
    except Exception:
        return []

def salvar_resposta_aluno(quiz_id, pergunta_id, usuario_id, alternativa_id, correta, indice_resposta):
    try:
        pontos = 1000.0 if correta else 0.0
        
        # 1. Verificar se o usuário já existe na tabela intermediária 'participantes_quiz' para este quiz
        id_participante_real = None
        try:
            res_part = supabase.table("participantes_quiz").select("id").eq("quiz_id", quiz_id).eq("usuario_id", usuario_id).execute()
            if res_part.data:
                id_participante_real = res_part.data[0]["id"]
            else:
                # Se não existir, insere o aluno na sessão para gerar o ID de participante correto
                res_novo_part = supabase.table("participantes_quiz").insert({
                    "quiz_id": quiz_id,
                    "usuario_id": usuario_id
                }).execute()
                if res_novo_part.data:
                    id_participante_real = res_novo_part.data[0]["id"]
        except Exception as e_part:
            # Fallback caso a tabela antiga use outra nomenclatura (ex: participante_id ou id_usuario)
            st.error(f"⚠️ Erro ao validar participante na sessão: {e_part}")
            return False

        if not id_participante_real:
            st.error("❌ Não foi possível vincular seu usuário à sessão ativa de participantes.")
            return False

        # 2. Envia o payload contendo a chave estrangeira correta gerada pelo banco antigo
        payload = {
            "quiz_id": quiz_id,
            "pergunta_id": pergunta_id,
            "usuario_id": usuario_id,
            "participante_id": id_participante_real,  # ✅ SOLUÇÃO: Agora enviando o ID da tabela correta!
            "alternativa_id": alternativa_id,
            "pontuacao_obtida": pontos,
            "indice_resposta": int(indice_resposta),
            "correta": bool(correta)
        }
        
        res = supabase.table("respostas_quiz").insert(payload).execute()
        return bool(res.data)
        
    except Exception as e:
        st.error(f"Erro estrutural no banco: {str(e)}")
        return False

def tela_quiz_rodada():
    usuario = st.session_state.get("usuario_logado", {})
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()
    user_id = usuario.get("id")
    quiz_id = st.session_state.get("quiz_ativo_id")

    if not quiz_id:
        st.warning("Nenhum quiz ativo selecionado.")
        if st.button("⬅️ Voltar ao Painel"):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
        return

    quiz = buscar_dados_quiz(quiz_id)
    if not quiz:
        st.error("Erro ao carregar dados da sala.")
        return

    # Sincronização automatizada via iframe no perfil do aluno (Long Pooling)
    if tipo == "aluno":
        st.iframe(
            src="data:text/html;charset=utf-8," + """
            <script>
                if (!window.refreshIntervalSet) {
                    window.refreshIntervalSet = true;
                    setInterval(function() { window.parent.postMessage({type: 'streamlit:setComponentValue', value: true}, '*'); }, 2000);
                }
            </script>
            """,
            height=1
        )

    st.title(f"🎮 {quiz.get('titulo')}")
    perguntas = buscar_perguntas_do_quiz(quiz_id)
    
    if not perguntas:
        st.info("Este quiz ainda não possui perguntas cadastradas.")
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
        return

    # Gerenciamento do ID da pergunta atual e etapas da rodada
    p_atual_id = quiz.get("pergunta_atual_id")
    etapa = quiz.get("etapa_rodada", "pergunta")

    # Se nenhuma pergunta foi disparada ainda (Sala de Espera)
    if not p_atual_id:
        if tipo in ("professor", "admin"):
            st.subheader("👨‍🏫 Painel de Moderação")
            st.info("A sala está cheia de alunos aguardando! Dispare a primeira questão para iniciar o show.")
            if st.button("🚀 Liberar Pergunta 1", type="primary", use_container_width=True):
                first_p = perguntas[0]["id"]
                supabase.table("quizzes").update({"pergunta_atual_id": first_p, "etapa_rodada": "pergunta"}).eq("id", quiz_id).execute()
                st.rerun()
        else:
            st.subheader("⏳ Aguardando o Professor...")
            st.info("Prepare sua mente! O professor iniciará a primeira rodada a qualquer momento.")
        return

    # Captura a pergunta ativa correspondente
    pergunta_ativa = next((p for p in perguntas if p["id"] == p_atual_id), perguntas[0])
    alternativas = buscar_alternativas(pergunta_ativa["id"])

    st.subheader(f"Questão {pergunta_ativa['ordem']}: {pergunta_ativa.get('enunciado') or pergunta_ativa.get('texto')}")
    
    # ------------------ VISÃO DO PROFESSOR ------------------
    if tipo in ("professor", "admin"):
        col1, col2 = st.columns(2)
        with col1:
            # 1º Passo: Bloquear submissões e revelar o Gabarito oficial na tela
            if etapa == "pergunta":
                if st.button("👁️ Mostrar Gabarito e Bloquear Respostas", type="primary", use_container_width=True):
                    supabase.table("quizzes").update({"etapa_rodada": "gabarito"}).eq("id", quiz_id).execute()
                    st.rerun()
            
            # 2º Passo: Verificar se há mais questões ou se encerra a partida síncrona
            else:
                idx_atual = next((i for i, p in enumerate(perguntas) if p["id"] == p_atual_id), 0)
                
                if idx_atual + 1 < len(perguntas):
                    if st.button("➡️ Avançar para Próxima Questão", type="primary", use_container_width=True):
                        prox_p = perguntas[idx_atual + 1]["id"]
                        supabase.table("quizzes").update({"pergunta_atual_id": prox_p, "etapa_rodada": "pergunta"}).eq("id", quiz_id).execute()
                        st.rerun()
                else:
                    if st.button("🛑 Encerrar Quiz e Mostrar Campeões", type="primary", use_container_width=True):
                        supabase.table("quizzes").update({"status": "finalizado"}).eq("id", quiz_id).execute()
                        st.session_state.quiz_ranking_id = quiz_id
                        st.session_state.pagina = "quiz_ranking_global"
                        st.rerun()
        with col2:
            if st.button("📊 Ver Telão de Líderes", use_container_width=True):
                st.session_state.quiz_ranking_id = quiz_id
                st.session_state.pagina = "quiz_ranking_global"
                st.rerun()

        st.markdown("---")
        for alt in alternativas:
            prefixo = "✅" if alt["correta"] else "❌"
            st.markdown(f"### {prefixo} {alt['texto']}")

# ------------------ VISÃO DO ALUNO (TRAVAMENTO DE RESPOSTA) ------------------
    else:
        if etapa == "pergunta":
            # 🛑 NOVIDADE: Checa se o aluno já respondeu esta questão específica nesta rodada
            ja_respondeu = False
            try:
                res_verificacao = supabase.table("respostas_quiz") \
                    .select("id") \
                    .eq("pergunta_id", pergunta_ativa["id"]) \
                    .eq("usuario_id", user_id) \
                    .execute()
                ja_respondeu = bool(res_verificacao.data)
            except Exception:
                pass

            # Se já respondeu, trava a tela com uma mensagem limpa
            if ja_respondeu:
                st.markdown("### 📥 Resposta Registrada com Sucesso!")
                st.info("Sua escolha foi guardada. Aguarde o professor encerrar o tempo para visualizar o gabarito oficial.")
            
            # Se ainda não respondeu, exibe os botões normalmente
            else:
                st.caption("⏱️ Escolha a alternativa correta antes do professor travar a rodada!")
                
                # Renderiza as 4 opções como botões dinâmicos de resposta
                for alt in alternativas:
                    if st.button(f"🔘 {alt['texto']}", key=f"btn_alt_{alt['id']}", use_container_width=True):
                        # Passa o alt['ordem'] correspondente para satisfazer a coluna indice_resposta do banco
                        sucesso = salvar_resposta_aluno(quiz_id, pergunta_ativa["id"], user_id, alt["id"], alt["correta"], alt["ordem"])
                        if sucesso:
                            st.toast("Resposta registrada com sucesso!", icon="✅")
                            time.sleep(0.5)
                            st.rerun()  # Dá um refresh para alternar o estado do front na hora
                        else:
                            st.error("Erro operacional ao salvar sua resposta. Tente novamente.")
        
        else:
            st.markdown("### 🔒 Rodada Encerrada pelo Docente!")
            # Validação imediata do acerto/erro baseado na resposta guardada
            try:
                resp = supabase.table("respostas_quiz").select("*, alternativas_quiz(correta, texto)").eq("pergunta_id", pergunta_ativa["id"]).eq("usuario_id", user_id).single().execute()
                if resp.data and resp.data["alternativas_quiz"]["correta"]:
                    st.success(f"🎉 Você ACERTOU! Resposta: {resp.data['alternativas_quiz']['texto']}")
                elif resp.data:
                    st.error(f"😞 Você ERROU! Você marcou: {resp.data['alternativas_quiz']['texto']}")
                else:
                    st.info("⏱️ O tempo acabou e você não enviou nenhuma resposta a tempo.")
            except Exception:
                st.info("Aguardando computação geral dos pontos no telão de líderes...")