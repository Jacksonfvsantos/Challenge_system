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

def salvar_resposta_aluno(quiz_id, pergunta_id, usuario_id, alternativa_id, correta):
    try:
        pontos = 1000.0 if correta else 0.0
        
        # Como o banco exige a string da resposta, vamos buscar o texto dela rapidamente
        texto_alternativa = "Alternativa Selecionada"
        try:
            res_alt = supabase.table("alternativas_quiz").select("texto").eq("id", alternativa_id).single().execute()
            if res_alt.data:
                texto_alternativa = res_alt.data["texto"]
        except Exception:
            pass

        # Inserção preenchendo tanto o modelo síncrono quanto todas as colunas NOT NULL antigas
        supabase.table("respostas_quiz").insert({
            "quiz_id": quiz_id,
            "pergunta_id": pergunta_id,
            "usuario_id": usuario_id,
            "participante_id": usuario_id,      # Coluna antiga NOT NULL 1
            "alternativa_id": alternativa_id,
            "pontuacao_obtida": pontos,
            "resposta": texto_alternativa,       # ✅ SOLUÇÃO: Coluna antiga NOT NULL 2
            "correta": bool(correta)            # ✅ SOLUÇÃO: Coluna antiga NOT NULL 3
        }).execute()
        return True
    except Exception as e:
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

    # Sincronização automatizada via iframe no perfil do aluno
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

    # Gerenciamento do ID da pergunta atual
    p_atual_id = quiz.get("pergunta_atual_id")
    etapa = quiz.get("etapa_rodada", "pergunta")

    # Se nenhuma pergunta foi disparada ainda
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

    st.subheader(f"Questão {pergunta_ativa['ordem']}: {pergunta_ativa['enunciado']}")
    
    # ------------------ VISÃO DO PROFESSOR (CORRIGIDA) ------------------
    if tipo in ("professor", "admin"):
        col1, col2 = st.columns(2)
        with col1:
            # 1º Passo independente da questão: Travar e mostrar o gabarito
            if etapa == "pergunta":
                if st.button("👁️ Mostrar Gabarito e Bloquear Respostas", type="primary", use_container_width=True):
                    supabase.table("quizzes").update({"etapa_rodada": "gabarito"}).eq("id", quiz_id).execute()
                    st.rerun()
            
            # 2º Passo (etapa == "gabarito"): Decidir se avança ou finaliza o quiz inteiro
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

    # ------------------ VISÃO DO ALUNO ------------------
    else:
        if etapa == "pergunta":
            st.caption("⏱️ Escolha a alternativa correta antes do professor travar a rodada!")
            
            # Renderiza as 4 opções como botões para o aluno clicar
            for alt in alternativas:
                if st.button(f"🔘 {alt['texto']}", key=f"btn_alt_{alt['id']}", use_container_width=True):
                    sucesso = salvar_resposta_aluno(quiz_id, pergunta_ativa["id"], user_id, alt["id"], alt["correta"])
                    if sucesso:
                        st.toast("Resposta registrada! Aguardando o gabarito do professor...", icon="📥")
                    else:
                        st.warning("Você já respondeu esta questão!")
        else:
            st.markdown("### 🔒 Rodada Encerrada!")
            # Verifica o que o aluno marcou
            try:
                resp = supabase.table("respostas_quiz").select("*, alternativas_quiz(correta, texto)").eq("pergunta_id", pergunta_ativa["id"]).eq("usuario_id", user_id).single().execute()
                if resp.data and resp.data["alternativas_quiz"]["correta"]:
                    st.success(f"🎉 Você ACERTOU! Resposta: {resp.data['alternativas_quiz']['texto']}")
                elif resp.data:
                    st.error(f"😞 Você ERROU! Você marcou: {resp.data['alternativas_quiz']['texto']}")
                else:
                    st.info("⏱️ O tempo acabou e você não enviou uma resposta.")
            except Exception:
                st.info("Aguardando computação geral dos pontos.")