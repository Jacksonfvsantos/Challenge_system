import streamlit as st
import time
from datetime import datetime, timezone
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

# 🔄 SENTINELA DE ATUALIZAÇÃO DA INTERFACE DO ALUNO
@st.fragment(run_every=2.0)
def executar_sincronia_aluno(quiz_id, etapa_atual, pergunta_atual_id):
    quiz_recente = buscar_dados_quiz(quiz_id)
    if not quiz_recente:
        return

    db_etapa = str(quiz_recente.get("etapa_rodada", "pergunta")).strip().lower()
    local_etapa = str(etapa_atual).strip().lower()
    
    db_pergunta = str(quiz_recente.get("pergunta_atual_id") or "").strip()
    local_pergunta = str(pergunta_atual_id or "").strip()

    if (db_etapa != local_etapa) or (db_pergunta != local_pergunta):
        st.rerun(scope="app")

# ⏱️ COMPONENTE DO CRONÔMETRO VISUAL DINÂMICO
@st.fragment(run_every=1.0)
def renderizar_cronometro_visual(quiz, tempo_limite, tipo_usuario, respostas_enviadas, total_alunos):
    """Atualiza visualmente os segundos na tela a cada 1.0s de forma isolada."""
    ultimo_update_str = quiz.get("updated_at") or quiz.get("data_resposta")
    if ultimo_update_str:
        try:
            ultimo_update_str = ultimo_update_str.replace("Z", "+00:00")
            segundos_decorridos = (datetime.now(timezone.utc) - datetime.fromisoformat(ultimo_update_str)).total_seconds()
            tempo_restante = max(int(tempo_limite - segundos_decorridos), 0)
        except Exception:
            tempo_restante = tempo_limite
    else:
        tempo_restante = tempo_limite

    # Exibe a métrica correspondente baseada em quem está olhando a tela
    if tipo_usuario in ("professor", "admin"):
        c1, c2 = st.columns(2)
        c1.metric(label="⏱️ Tempo Restante", value=f"{tempo_restante}s")
        c2.metric(label="📥 Respostas Recebidas", value=f"{respostas_enviadas} de {total_alunos}")
    else:
        st.metric(label="⏱️ Tempo Restante para Responder", value=f"{tempo_restante} segundos")

    # Se o tempo zerar dentro do fragmento, força o script principal a validar o encerramento
    if tempo_restante <= 0:
        st.rerun(scope="app")

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

    # 🚪 SALA DE ESPERA
    if not p_atual_id:
        if tipo in ("professor", "admin"):
            st.subheader("👨‍🏫 Painel de Moderação")
            st.info("Alunos conectados aguardando! Clique abaixo para disparar o quiz.")
            if st.button("🚀 Iniciar Quiz (Pergunta 1)", type="primary", use_container_width=True, key="btn_trigger_first_q"):
                first_p = perguntas[0]["id"]
                supabase.table("quizzes").update({
                    "pergunta_atual_id": first_p, 
                    "etapa_rodada": "pergunta",
                    "status": "ativo"
                }).eq("id", quiz_id).execute()
                st.rerun()
        else:
            st.subheader("⏳ Sala de Espera")
            st.info("Conectado com sucesso! Aguarde o professor dar início à partida.")
            executar_sincronia_aluno(quiz_id, etapa, p_atual_id)
        return

    pergunta_ativa = next((p for p in perguntas if p["id"] == p_atual_id), perguntas[0])
    alternativas = buscar_alternativas(pergunta_ativa["id"])
    tempo_limite = int(pergunta_ativa.get("tempo_limite_segundos", 30))

    respostas_enviadas, total_alunos = contar_respostas_e_participantes(quiz_id, pergunta_ativa["id"])

    # 🚨 MOTOR DE VERIFICAÇÃO EM TEMPO DE EXECUÇÃO (Sem sleep para não dar lag)
    if etapa == "pergunta":
        ultimo_update_str = quiz.get("updated_at") or quiz.get("data_resposta")
        if ultimo_update_str:
            try:
                ultimo_update_str = ultimo_update_str.replace("Z", "+00:00")
                decorrido = (datetime.now(timezone.utc) - datetime.fromisoformat(ultimo_update_str)).total_seconds()
            except Exception:
                decorrido = 0
        else:
            decorrido = 0

        todos_responderam = respostas_enviadas >= total_alunos and total_alunos > 0
        if (decorrido >= tempo_limite) or todos_responderam:
            supabase.table("quizzes").update({"etapa_rodada": "gabarito"}).eq("id", quiz_id).execute()
            st.rerun()

    if tipo == "aluno":
        executar_sincronia_aluno(quiz_id, etapa, p_atual_id)

    st.subheader(f"Questão {pergunta_ativa['ordem']}: {pergunta_ativa.get('enunciado') or pergunta_ativa.get('texto')}")

    # ⏱️ Renderiza o cronômetro dinâmico isolado se a rodada estiver aberta
    if etapa == "pergunta":
        renderizar_cronometro_visual(quiz, tempo_limite, tipo, respostas_enviadas, total_alunos)

    # ------------------ VISÃO DO PROFESSOR ------------------
    if tipo in ("professor", "admin"):
        col1, col2 = st.columns(2)
        with col1:
            if etapa == "pergunta":
                if st.button("👁️ Forçar Encerramento Manual", type="secondary", use_container_width=True, key="btn_lock_and_reveal"):
                    supabase.table("quizzes").update({"etapa_rodada": "gabarito"}).eq("id", quiz_id).execute()
                    st.rerun()
            else:
                idx_atual = next((i for i, p in enumerate(perguntas) if p["id"] == p_atual_id), 0)
                if idx_atual + 1 < len(perguntas):
                    if st.button("➡️ Avançar para Próxima Questão", type="primary", use_container_width=True, key="btn_next_question_act"):
                        prox_p = perguntas[idx_atual + 1]["id"]
                        supabase.table("quizzes").update({
                            "pergunta_atual_id": prox_p, 
                            "etapa_rodada": "pergunta"
                        }).eq("id", quiz_id).execute()
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
                st.info("Aguardando o encerramento do tempo regulamentar...")
            else:
                st.caption("Selecione a opção correta:")
                for alt in alternativas:
                    if st.button(f"🔘 {alt['texto']}", key=f"btn_submit_alt_{alt['id']}", use_container_width=True):
                        sucesso = salvar_resposta_aluno(quiz_id, pergunta_ativa["id"], user_id, alt["id"], alt["correta"], alt["ordem"])
                        if sucesso:
                            st.toast("Resposta registrada!", icon="✅")
                            st.rerun()
        else:
            st.markdown("### 🔒 Rodada Encerrada!")
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
                    st.warning(f"⏱️ **Tempo esgotado, nenhuma alternativa escolhida!**\n\n**Gabarito Correto:** {text_correto}")
            except Exception:
                st.info(f"Gabarito oficial: {text_correto}")