import streamlit as st
import time
from database.conexao import supabase

def buscar_dados_quiz(quiz_id):
    try:
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

def contar_respostas_e_participantes(quiz_id, pergunta_id):
    """Retorna o total de alunos que responderam e o total de participantes na sala de forma segura."""
    try:
        res_parts = supabase.table("participantes_quiz").select("id").eq("quiz_id", quiz_id).execute()
        res_resps = supabase.table("respostas_quiz").select("id").eq("pergunta_id", pergunta_id).execute()
        
        total_parts = len(res_parts.data) if res_parts.data else 0
        total_resps = len(res_resps.data) if res_resps.data else 0
        
        return total_resps, max(total_parts, 1)
    except Exception:
        return 0, 1

def salvar_resposta_aluno(quiz_id, pergunta_id, usuario_id, alternativa_id, correta, indice_resposta):
    try:
        pontos = 1000.0 if correta else 0.0
        
        id_participante_real = None
        try:
            res_part = supabase.table("participantes_quiz").select("id").eq("quiz_id", quiz_id).eq("usuario_id", usuario_id).execute()
            if res_part.data:
                id_participante_real = res_part.data[0]["id"]
            else:
                res_novo_part = supabase.table("participantes_quiz").insert({
                    "quiz_id": quiz_id,
                    "usuario_id": usuario_id
                }).execute()
                if res_novo_part.data:
                    id_participante_real = res_novo_part.data[0]["id"]
        except Exception:
            return False

        if not id_participante_real:
            return False

        payload = {
            "quiz_id": quiz_id,
            "pergunta_id": pergunta_id,
            "usuario_id": usuario_id,
            "participante_id": id_participante_real,
            "alternativa_id": alternativa_id,
            "pontuacao_obtida": pontos,
            "indice_resposta": int(indice_resposta),
            "correta": bool(correta)
        }
        
        res = supabase.table("respostas_quiz").insert(payload).execute()
        return bool(res.data)
    except Exception:
        return False

# 🔄 SENTINELA DE AUTOMAÇÃO DE FLUXO (RODA EM SEGUNDO PLANO DE FORMA CONTROLADA)
@st.fragment
def executar_sincronia_automatica(quiz_id, etapa_atual, pergunta_atual_id):
    """Monitora o banco a cada 2.5s. Redesenha o app se houver mudanças estruturais."""
    time.sleep(2.5)
    quiz_recente = buscar_dados_quiz(quiz_id)
    if not quiz_recente:
        return

    # Se o professor alterou o estado na outra ponta, força a atualização global da UI
    if (quiz_recente.get("etapa_rodada") != etapa_atual) or (quiz_recente.get("pergunta_atual_id") != pergunta_atual_id):
        st.rerun(scope="app")

    # Regra de fechamento automático Kahoot (Apenas se a rodada já tiver uma pergunta ativa)
    if etapa_atual == "pergunta" and pergunta_atual_id:
        respostas, participantes = contar_respostas_e_participantes(quiz_id, pergunta_atual_id)
        if respostas >= participantes and participantes > 0:
            supabase.table("quizzes").update({"etapa_rodada": "gabarito"}).eq("id", quiz_id).execute()
            st.rerun(scope="app")
        else:
            # Atualiza apenas o fragmento para renovar o visual das barras de progresso
            st.rerun()

def tela_quiz_rodada():
    usuario = st.session_state.get("usuario_logado", {})
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()
    user_id = usuario.get("id")
    quiz_id = st.session_state.get("quiz_ativo_id")

    if not quiz_id:
        st.warning("Nenhum quiz ativo selecionado.")
        if st.button("⬅️ Voltar ao Painel", key="btn_back_err_state"):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
        return

    quiz = buscar_dados_quiz(quiz_id)
    if not quiz:
        st.error("Erro ao carregar dados da sala.")
        return

    p_atual_id = quiz.get("pergunta_atual_id")
    etapa = quiz.get("etapa_rodada", "pergunta")

    st.title(f"🎮 {quiz.get('titulo')}")
    perguntas = buscar_perguntas_do_quiz(quiz_id)
    
    if not perguntas:
        st.info("Este quiz ainda não possui perguntas cadastradas.")
        if st.button("⬅️ Voltar", key="btn_back_no_questions"):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
        return

    # 🚪 SALA DE ESPERA (BLINDADA CONTRA LOOPS INFINITOS)
    if not p_atual_id:
        if tipo in ("professor", "admin"):
            st.subheader("👨‍🏫 Painel de Moderação")
            st.info("Alunos conectados aguardando! Clique abaixo para disparar o quiz.")
            if st.button("🚀 Iniciar Quiz (Pergunta 1)", type="primary", use_container_width=True, key="btn_trigger_first_q"):
                first_p = perguntas[0]["id"]
                supabase.table("quizzes").update({"pergunta_atual_id": first_p, "etapa_rodada": "pergunta"}).eq("id", quiz_id).execute()
                st.rerun()
        else:
            st.subheader("⏳ Sala de Espera")
            st.info("Conectado com sucesso! Aguarde o professor dar início à partida.")
            # ✅ SOLUÇÃO: O aluno usa o fragmento seguro aqui também em vez de um st.rerun() solto
            executar_sincronia_automatica(quiz_id, etapa, p_atual_id)
        return

    pergunta_ativa = next((p for p in perguntas if p["id"] == p_atual_id), perguntas[0])
    alternativas = buscar_alternativas(pergunta_ativa["id"])

    # Sentinela ativo durante a exibição das questões
    executar_sincronia_automatica(quiz_id, etapa, p_atual_id)

    st.subheader(f"Questão {pergunta_ativa['ordem']}: {pergunta_ativa.get('enunciado') or pergunta_ativa.get('texto')}")
    respostas_enviadas, total_alunos = contar_respostas_e_participantes(quiz_id, pergunta_ativa["id"])

    # ------------------ VISÃO DO PROFESSOR ------------------
    if tipo in ("professor", "admin"):
        st.metric(label="Respostas Recebidas", value=f"{respostas_enviadas} de {total_alunos} alunos")
        
        col1, col2 = st.columns(2)
        with col1:
            if etapa == "pergunta":
                if st.button("👁️ Forçar Encerramento e Ver Gabarito", type="secondary", use_container_width=True, key="btn_lock_and_reveal"):
                    supabase.table("quizzes").update({"etapa_rodada": "gabarito"}).eq("id", quiz_id).execute()
                    st.rerun()
            else:
                idx_atual = next((i for i, p in enumerate(perguntas) if p["id"] == p_atual_id), 0)
                if idx_atual + 1 < len(perguntas):
                    if st.button("➡️ Avançar para Próxima Questão", type="primary", use_container_width=True, key="btn_next_question_act"):
                        prox_p = perguntas[idx_atual + 1]["id"]
                        supabase.table("quizzes").update({"pergunta_atual_id": prox_p, "etapa_rodada": "pergunta"}).eq("id", quiz_id).execute()
                        st.rerun()
                else:
                    if st.button("🛑 Finalizar Quiz e Ver Pódio", type="primary", use_container_width=True, key="btn_finish_quiz_global"):
                        supabase.table("quizzes").update({"status": "finalizado"}).eq("id", quiz_id).execute()
                        st.session_state.quiz_ranking_id = quiz_id
                        st.session_state.pagina = "quiz_ranking_global"
                        st.rerun()
        with col2:
            if st.button("📊 Ver Telão de Líderes", use_container_width=True, key="btn_view_leaders_mid"):
                st.session_state.quiz_ranking_id = quiz_id
                st.session_state.pagina = "quiz_ranking_global"
                st.rerun()

        st.markdown("---")
        st.write("📋 **Gabarito de Referência (Oculto para Alunos):**")
        for alt in alternativas:
            prefixo = "✅" if alt["correta"] else "❌"
            st.markdown(f"### {prefixo} {alt['texto']}")

    # ------------------ VISÃO DO ALUNO ------------------
    else:
        if etapa == "pergunta":
            progresso_respostas = min(respostas_enviadas / total_alunos, 1.0)
            st.progress(progresso_respostas, text=f"📥 {respostas_enviadas}/{total_alunos} alunos já responderam...")

            ja_respondeu = False
            try:
                res_verificacao = supabase.table("respostas_quiz").select("id").eq("pergunta_id", pergunta_ativa["id"]).eq("usuario_id", user_id).execute()
                ja_respondeu = bool(res_verificacao.data)
            except Exception:
                pass

            if ja_respondeu:
                st.markdown("### 📥 Resposta Registrada com Sucesso!")
                st.info("Aguardando os demais participantes concluírem para revelar o gabarito...")
            else:
                st.caption("Selecione a opção correta:")
                for alt in alternativas:
                    if st.button(f"🔘 {alt['texto']}", key=f"btn_submit_alt_{alt['id']}", use_container_width=True):
                        sucesso = salvar_resposta_aluno(quiz_id, pergunta_ativa["id"], user_id, alt["id"], alt["correta"], alt["ordem"])
                        if sucesso:
                            st.toast("Resposta registrada!", icon="✅")
                            time.sleep(0.3)
                            st.rerun()
        else:
            st.markdown("### 🔒 Tempo Esgotado! Conferindo Resultados...")
            st.markdown("---")
            
            alt_correta = next((a for a in alternativas if a["correta"]), None)
            text_correto = alt_correta["texto"] if alt_correta else ""

            try:
                resp = supabase.table("respostas_quiz").select("alternativa_id, correta").eq("pergunta_id", pergunta_ativa["id"]).eq("usuario_id", user_id).execute()
                
                if resp.data:
                    aluno_acertou = resp.data[0]["correta"]
                    id_marcado = resp.data[0]["alternativa_id"]
                    alt_marcada = next((a for a in alternativas if a["id"] == id_marcado), None)
                    text_marcado = alt_marcada["texto"] if alt_marcada else ""

                    if aluno_acertou:
                        st.success(f"🎉 **Você ACERTOU!**\n\n**Sua Resposta:** {text_marcado}")
                    else:
                        st.error(f"😞 **Você ERROU!**\n\n**Você marcou:** {text_marcado}\n\n**Gabarito Correto:** {text_correto}")
                else:
                    st.warning(f"⏱️ **O tempo acabou!** Você não enviou nenhuma resposta.\n\n**Gabarito Correto:** {text_correto}")
            except Exception:
                st.info(f"Gabarito oficial: {text_correto}")