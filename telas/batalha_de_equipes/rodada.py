import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

# --- FUNÇÕES DE SUPORTE AO BACKEND DA RODADA ---

def obter_estado_batalha(batalha_id):
    try:
        res = supabase.table("batalhas").select("*, times:time_da_vez_id(nome)").eq("id", batalha_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def obter_pergunta_atual(batalha_id, ordem_pergunta):
    try:
        vinculo = (
            supabase
            .table("batalha_perguntas")
            .select("questao_id")
            .eq("batalha_id", batalha_id)
            .eq("ordem", ordem_pergunta)
            .execute()
        )
        if not vinculo.data:
            return None
            
        q_id = vinculo.data[0]["questao_id"]
        
        questao = supabase.table("questoes").select("*").eq("id", q_id).execute()
        alternativas = supabase.table("alternativas").select("*").eq("questao_id", q_id).order("ordem").execute()
        
        return {
            "id": q_id,
            "enunciado": questao.data[0]["enunciado"] if questao.data else "Questão não encontrada",
            "alternativas": alternativas.data or []
        }
    except Exception:
        return None

def obter_time_do_usuario(usuario_id):
    try:
        res = supabase.table("time_membros").select("time_id, times(nome)").eq("usuario_id", usuario_id).execute()
        if res.data:
            return res.data[0]["time_id"], res.data[0]["times"]["nome"]
        return None, None
    except Exception:
        return None, None

def processar_resposta_sincrona(batalha_id, questao_id, time_id, alternativa_correta, time_adversario_id, tentativa_atual):
    """
    Processa a escolha da alternativa feita por um participante.
    Regras do Bate-Rebate:
    - Se acertar: ganha ponto, avança de pergunta e passa a vez para o adversário começar a próxima.
    - Se errar na 1ª tentativa: ativa o REBATE, passando a vez da mesma pergunta para o adversário.
    - Se errar na 2ª tentativa (Rebate): ambos erraram, avança de pergunta e mantém a posse com quem tentou o rebate.
    """
    try:
        # Grava o histórico da resposta no banco
        supabase.table("batalha_respostas").insert({
            "batalha_id": batalha_id,
            "questao_id": questao_id,
            "time_id": time_id,
            "resposta_correta": alternativa_correta,
            "tentativa_numero": tentativa_atual
        }).execute()

        if alternativa_correta:
            batalha = obter_estado_batalha(batalha_id)
            proxima_ordem = batalha["pergunta_atual_ordem"] + 1
            
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": proxima_ordem,
                "status_sincrono": "aguardando_resposta",
                "time_da_vez_id": time_adversario_id  # Passa a vez de começar a próxima questão
            }).eq("id", batalha_id).execute()
            return "acertou"
        else:
            if tentativa_atual == 1:
                # Ativa o modo rebate para o adversário responder a MESMA questão
                supabase.table("batalhas").update({
                    "status_sincrono": "rebate_ativo",
                    "time_da_vez_id": time_adversario_id
                }).eq("id", batalha_id).execute()
                return "rebate"
            else:
                # Se errou a segunda tentativa (o rebate), passa para a próxima questão
                batalha = obter_estado_batalha(batalha_id)
                proxima_ordem = batalha["pergunta_atual_ordem"] + 1
                
                supabase.table("batalhas").update({
                    "pergunta_atual_ordem": proxima_ordem,
                    "status_sincrono": "aguardando_resposta",
                    "time_da_vez_id": time_id
                }).eq("id", batalha_id).execute()
                return "ambos_erraram"
    except Exception as e:
        print(f"❌ Erro [processar_resposta_sincrona]: {e}")
        return "erro"

# --- INTERFACE VISUAL STREAMLIT ---

def tela_batalha_rodada():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    # Trava para alunos sem equipa cadastrada
    if tipo_usuario == "aluno":
        time_id, time_nome = obter_time_do_usuario(usuario_id)
        if not time_id:
            st.error("🛑 Acesso Negado: Precisa de fazer parte de uma equipa para entrar na partida!")
            if st.button("🏢 Criar minha Equipe Agora", type="primary", use_container_width=True):
                st.session_state.pagina = "batalha_times"
                st.rerun()
            return

    # Polling de sincronização automática (3 segundos)
    st.caption("🔄 Sincronização automática ativa (3s)")
    time.sleep(3)
    
    if "batalha_ativa_id" not in st.session_state:
        try:
            res = supabase.table("batalhas").select("id").eq("finalizada", False).execute()
            if res.data:
                st.session_state.batalha_ativa_id = res.data[0]["id"]
            else:
                st.warning("Nenhuma batalha ativa localizada no momento.")
                return
        except Exception:
            return

    batalha_id = st.session_state.batalha_ativa_id
    batalha = obter_estado_batalha(batalha_id)
    
    if not batalha or batalha.get("finalizada") is True or str(batalha.get("status")).lower() == "finalizada":
        st.success("🎉 A batalha foi encerrada! Verifique o placar final com o professor.")
        if st.button("Voltar para a Arena", use_container_width=True):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    cabecalho(f"⚔️ Partida Síncrona: {batalha['titulo']}", "Modo de Jogo: Bate-Rebate")

    # --- CONTROLO DO PROFESSOR (LOBBY) ---
    if tipo_usuario in ("professor", "admin") and str(batalha.get("status")).lower() == "agendada":
        st.markdown("### 🎛️ Painel de Controle de Início da Partida")
        time_a_id = batalha.get("time_a_id")
        time_b_id = batalha.get("time_b_id")
        
        try:
            res_times = supabase.table("times").select("id, nome").in_("id", [time_a_id, time_b_id]).execute()
            lista_times_sala = res_times.data or []
        except Exception:
            lista_times_sala = []
            
        if not lista_times_sala:
            st.error("🛑 Erro: As duas equipas escaladas não foram encontradas.")
        else:
            time_inicial = st.selectbox(
                "Selecione a Equipe que inicia jogando:",
                options=lista_times_sala,
                format_func=lambda x: str(x["nome"]).strip(),
                key="select_time_inicial_batalha"
            )
            
            from services.batalha_service import iniciar_partida_sincrona
            if st.button("🔥 Começar Partida Agora!", type="primary", use_container_width=True):
                if iniciar_partida_sincrona(batalha_id, time_inicial["id"]):
                    st.success("🚀 Partida iniciada!")
                    st.rerun()
        st.markdown("---")
        return

    # --- LOBBY DE ESPERA DO ALUNO ---
    if tipo_usuario == "aluno" and str(batalha.get("status")).lower() == "agendada":
        st.info("⏳ **Sala de Espera:** Aguarde o professor dar o início à partida...")
        return

    # --- RESOLUÇÃO DE PAPÉIS DA PARTIDA ---
    if tipo_usuario == "aluno":
        time_id, time_nome = obter_time_do_usuario(usuario_id)
        # Valida se o aluno faz parte do confronto
        if str(time_id) != str(batalha.get("time_a_id")) and str(time_id) != str(batalha.get("time_b_id")):
            st.warning("👁️ Modo Espectador: A sua equipa não está escalada para esta disputa.")
            eh_espectador = True
        else:
            eh_espectador = False
    else:
        # Se for professor, ele assiste e monitoriza as ações
        time_id, time_nome = "PROFESSOR_CONSOLA", "Painel Docente"
        eh_espectador = True

    # Define quem é o adversário direto para o rebate
    time_adversario_id = batalha.get("time_b_id") if str(time_id) == str(batalha.get("time_a_id")) else batalha.get("time_a_id")
    
    time_da_vez_id = batalha.get("time_da_vez_id")
    status_sincrono = batalha.get("status_sincrono", "aguardando_resposta")
    pergunta_ordem = batalha.get("pergunta_atual_ordem", 1)
    
    tentativa_atual = 2 if status_sincrono == "rebate_ativo" else 1
    eh_a_vez_deste_time = (str(time_id) == str(time_da_vez_id))

    st.markdown(f"### 📍 Pergunta Atual: N° {pergunta_ordem}")
    
    # Painéis de feedback visual de turno
    if tipo_usuario == "aluno" and not eh_espectador:
        if eh_a_vez_deste_time:
            st.markdown(f"""
            <div style="background-color: #065f46; border-left: 6px solid #10b981; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="color: #a7f3d0; margin: 0;">🟢 É A VEZ DO SEU TIME! ({time_nome})</h4>
                <p style="color: #a7f3d0; margin: 5px 0 0 0; font-size: 14px;">
                    Sua equipe está com o controle. Tentativa: <strong>{tentativa_atual}ª Chance</strong> {"(REBATE ATIVO!)" if tentativa_atual == 2 else ""}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            nome_time_vez = batalha.get("times", {}).get("nome", "Adversário") if batalha.get("times") else "Adversário"
            st.markdown(f"""
            <div style="background-color: #7c2d12; border-left: 6px solid #ea580c; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="color: #ffedd5; margin: 0;">⏱️ AGUARDANDO ADVERSÁRIO...</h4>
                <p style="color: #ffedd5; margin: 5px 0 0 0; font-size: 14px;">
                    O time <strong>{nome_time_vez}</strong> está respondendo agora.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # --- RENDERIZAÇÃO DA QUESTÃO E ALTERNATIVAS ---
    dados_pergunta = obter_pergunta_atual(batalha_id, pergunta_ordem)
    
    if not dados_pergunta:
        st.info("🏁 Parabéns! Chegamos ao fim das perguntas preparadas para esta rodada.")
        if st.button("Voltar para Arena", use_container_width=True):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    with st.container(border=True):
        st.markdown(f"**Enunciado:**\n{dados_pergunta['enunciado']}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Selecione a alternativa correta:**")
    
    # Renderiza os botões das alternativas. Ficam desativados se não for a vez do participante.
    for alt in dados_pergunta["alternativas"]:
        letra_ordem = chr(64 + int(alt["ordem"]))
        texto_opcao = f"{letra_ordem}) {alt['texto']}"
        
        # Apenas clica se for a vez do time dele E não for mero espectador/professor
        liberado_para_clique = eh_a_vez_deste_time and (not eh_espectador)
        
        if st.button(texto_opcao, key=f"alt_{alt['id']}", use_container_width=True, disabled=not liberado_para_clique):
            resultado = processar_resposta_sincrona(
                batalha_id, 
                dados_pergunta["id"], 
                time_id, 
                alt["correta"], 
                time_adversario_id,
                tentativa_atual
            )
            
            if resultado == "acertou":
                st.toast("🎉 Excelente! Sua equipe acertou e garantiu o ponto!", icon="🔥")
            elif resultado == "rebate":
                st.toast("❌ Errado! O Rebate foi ativado. A bola passou para o adversário!", icon="⚠️")
            elif resultado == "ambos_erraram":
                st.toast("🛑 Ambos falharam nesta questão. Avançando de round...", icon="💀")
                
            time.sleep(1)
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Sair da Partida", type="secondary", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()