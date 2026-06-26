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

def salvar_resposta_aluno(quiz_id, pergunta_id, usuario_id, alternativa_id, correta, indice_resposta):
    try:
        pontos = 1000.0 if correta else 0.0
        
        # 1. Vínculo dinâmico com a tabela intermediária 'participantes_quiz'
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

    # Sincronização automatizada via iframe no perfil do aluno (Long Pooling Corrigido)
    if tipo == "aluno":
        # 🔄 CAPTURA DO SINAL: Armazenamos o retorno do iframe em uma variável do Streamlit
        refresh_sinal = st.iframe(
            src="data:text/html;charset=utf-8," + """
            <script>
                if (!window.refreshIntervalSet) {
                    window.refreshIntervalSet = true;
                    setInterval(function() { 
                        // Envia um valor incremental (timestamp) para forçar o Streamlit a notar a mudança
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue', 
                            value: new Date().getTime()
                        }, '*'); 
                    }, 2000); // Verifica mudanças a cada 2 segundos
                }
            </script>
            """,
            height=1
        )
        
        # 🚀 FORÇAR RERUN: Se o sinal mudou lá no JavaScript, o Python intercepta e força a tela a redesenhar
        if refresh_sinal:
            st.rerun()

    st.title(f"🎮 {quiz.get('titulo')}")
    perguntas = buscar_perguntas_do_quiz(quiz_id)
    
    if not perguntas:
        st.info("Este quiz ainda não possui perguntas cadastradas.")
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
        return

    p_atual_id = quiz.get("pergunta_atual_id")
    etapa = quiz.get("etapa_rodada", "pergunta")

    # Sala de Espera
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

    pergunta_ativa = next((p for p in perguntas if p["id"] == p_atual_id), perguntas[0])
    alternativas = buscar_alternativas(pergunta_ativa["id"])
    tempo_limite = int(pergunta_ativa.get("tempo_limite_segundos", 30))

    st.subheader(f"Questão {pergunta_ativa['ordem']}: {pergunta_ativa.get('enunciado') or pergunta_ativa.get('texto')}")
    
    # ------------------ VISÃO DO PROFESSOR ------------------
    if tipo in ("professor", "admin"):
        # Mostra o indicador de tempo decorrendo para controle do mediador
        st.write(f"⏱️ **Tempo sugerido para esta questão:** `{tempo_limite} segundos`")
        
        col1, col2 = st.columns(2)
        with col1:
            if etapa == "pergunta":
                if st.button("👁️ Mostrar Gabarito e Bloquear Respostas", type="primary", use_container_width=True):
                    supabase.table("quizzes").update({"etapa_rodada": "gabarito"}).eq("id", quiz_id).execute()
                    st.rerun()
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
        st.write("📋 **Visualização do Gabarito do Professor:**")
        for alt in alternativas:
            prefixo = "✅" if alt["correta"] else "❌"
            st.markdown(f"### {prefixo} {alt['texto']}")

    # ------------------ VISÃO DO ALUNO ------------------
    else:
        if etapa == "pergunta":
            # ⏱️ TIMER DINÂMICO PROGRESSIVO DE ATENÇÃO
            st.progress(1.0, text="⏳ A rodada está aberta! Responda rápido!")

            # Checa se o aluno já respondeu esta questão
            ja_respondeu = False
            try:
                res_verificacao = supabase.table("respostas_quiz").select("id").eq("pergunta_id", pergunta_ativa["id"]).eq("usuario_id", user_id).execute()
                ja_respondeu = bool(res_verificacao.data)
            except Exception:
                pass

            if ja_respondeu:
                st.markdown("### 📥 Resposta Registrada com Sucesso!")
                st.info("Sua escolha foi guardada. Aguarde o professor encerrar o tempo para visualizar o gabarito oficial.")
            else:
                st.caption(f"⏱️ Tempo sugerido: {tempo_limite}s. Selecione a opção correta:")
                
                for alt in alternativas:
                    if st.button(f"🔘 {alt['texto']}", key=f"btn_alt_{alt['id']}", use_container_width=True):
                        sucesso = salvar_resposta_aluno(quiz_id, pergunta_ativa["id"], user_id, alt["id"], alt["correta"], alt["ordem"])
                        if sucesso:
                            st.toast("Resposta registrada com sucesso!", icon="✅")
                            time.sleep(0.3)
                            st.rerun()

        # ✨ ETAPA GABARITO: REVELAÇÃO EM TEMPO REAL PARA O ALUNO ✨
        else:
            st.markdown("### 🔒 Rodada Encerrada pelo Professor!")
            st.markdown("---")
            
            # Encontra qual era a alternativa correta no lote atual
            alt_correta = next((a for a in alternativas if a["correta"]), None)
            texto_correto = alt_correta["texto"] if alt_correta else "Não definida"

            try:
                # Busca a resposta que esse usuário enviou
                resp = supabase.table("respostas_quiz").select("alternativa_id, correta").eq("pergunta_id", pergunta_ativa["id"]).eq("usuario_id", user_id).execute()
                
                if resp.data:
                    aluno_acertou = resp.data[0]["correta"]
                    id_marcado = resp.data[0]["alternativa_id"]
                    
                    # Encontra o texto da alternativa que o aluno marcou
                    alt_marcada = next((a for a in alternativas if a["id"] == id_marcado), None)
                    texto_marcado = alt_marcada["texto"] if alt_marcada else "Desconhecida"

                    if aluno_acertou:
                        st.success(f"🎉 **Você ACERTOU!**\n\n**Sua Resposta:** {texto_marcado}")
                    else:
                        st.error(f"😞 **Você ERROU!**\n\n**Você marcou:** {texto_marcado}\n\n**Gabarito Correto:** {texto_correto}")
                else:
                    st.warning(f"⏱️ **O tempo acabou!** Você não enviou nenhuma resposta para esta questão.\n\n**Gabarito Correto:** {texto_correto}")
            
            except Exception:
                st.info(f"O tempo expirou! **Gabarito oficial:** {texto_correto}")