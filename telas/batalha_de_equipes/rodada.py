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
    try:
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
                "time_da_vez_id": time_adversario_id
            }).eq("id", batalha_id).execute()
            return "acertou"
        else:
            if tentativa_atual == 1:
                supabase.table("batalhas").update({
                    "status_sincrono": "rebate_ativo",
                    "time_da_vez_id": time_adversario_id
                }).eq("id", batalha_id).execute()
                return "rebate"
            else:
                batalha = obter_estado_batalha(batalha_id)
                proxima_ordem = batalha["pergunta_atual_ordem"] + 1
                
                supabase.table("batalhas").update({
                    "pergunta_atual_ordem": proxima_ordem,
                    "status_sincrono": "aguardando_resposta",
                    "time_da_vez_id": time_id
                }).eq("id", batalha_id).execute()
                return "ambos_erraram"
    except Exception:
        return "erro"

# --- INTERFACE VISUAL STREAMLIT ---

def tela_batalha_rodada():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    # ------------------------------------------------------------------------
    # 🛡️ TRAVA DE SEGURANÇA: ALUNOS SEM EQUIPE SÃO BARRADOS NO PORTÃO
    # ------------------------------------------------------------------------
    if tipo_usuario == "aluno":
        time_id, time_nome = obter_time_do_usuario(usuario_id)
        if not time_id:
            st.error("🛑 Acesso Negado: Você precisa fazer parte de uma equipe para entrar na partida síncrona!")
            st.info("Fundamente um novo time ou solicite sua alocação antes de entrar na sala de disputas.")
            
            if st.button("🏢 Criar minha Equipe Agora", type="primary", use_container_width=True):
                st.session_state.pagina = "batalha_times"
                st.rerun()
                
            if st.button("⬅️ Voltar para a Arena", use_container_width=True):
                st.session_state.pagina = "batalha_de_equipes"
                st.rerun()
            return

    # Polling automático (Atualização de tela a cada 3s)
    st.caption("🔄 Sincronização automática ativa (3s)")
    time.sleep(3)
    
    if "batalha_ativa_id" not in st.session_state:
        try:
            res = supabase.table("batalhas").select("id").eq("finalizada", False).execute()
            if res.data:
                st.session_state.batalha_ativa_id = res.data[0]["id"]
            else:
                st.warning("Nenhuma batalha ativa localizada pelo sistema no momento.")
                if st.button("⬅️ Voltar ao Menu"):
                    st.session_state.pagina = "batalha_de_equipes"
                    st.rerun()
                return
        except Exception:
            return

    batalha_id = st.session_state.batalha_ativa_id
    batalha = obter_estado_batalha(batalha_id)
    
    # ------------------------------------------------------------------------
    # ⚙️ BUGFIX CRÍTICO: Validação estrita e segura do status de encerramento
    # ------------------------------------------------------------------------
    if not batalha or batalha.get("finalizada") is True or str(batalha.get("status")).lower() == "finalizada":
        st.success("🎉 A batalha foi encerrada! Verifique o placar final com o professor.")
        if st.button("Voltar para a Arena", use_container_width=True):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    cabecalho(f"⚔️ Partida Síncrona: {batalha['titulo']}", "Modo de Jogo atual: Bate-Rebate")

    # ------------------------------------------------------------------------
    # 🎮 PAINEL DE INICIALIZAÇÃO EXCLUSIVO DO PROFESSOR (DUAS EQUIPES ALVO)
    # ------------------------------------------------------------------------
    if tipo_usuario in ("professor", "admin") and str(batalha.get("status")).lower() == "agendada":
        st.markdown("### 🎛️ Painel de Controle de Início da Partida")
        st.info("A batalha está aguardando seu comando para começar. Escolha qual das duas equipes iniciará atacando:")
        
        # Puxa estritamente os dois times escalados para essa batalha específica
        time_a_id = batalha.get("time_a_id")
        time_b_id = batalha.get("time_b_id")
        
        try:
            res_times = supabase.table("times").select("id, nome").in_("id", [time_a_id, time_b_id]).execute()
            lista_times_sala = res_times.data or []
        except Exception:
            lista_times_sala = []
            
        if not lista_times_sala:
            st.error("🛑 Erro: As duas equipes escaladas para este confronto não foram encontradas no banco.")
        else:
            # Localize este bloco por volta da linha 142 no seu rodada.py:
            time_inicial = st.selectbox(
                "Selecione a Equipe que inicia jogando:",
                options=lista_times_sala,
                format_func=lambda x: str(x["nome"]).strip(), # ✅ Extrai apenas o nome amigável do time
                key="select_time_inicial_batalha"
            )
            
            from services.batalha_service import iniciar_partida_sincrona
            
            if st.button("🔥 Começar Partida Agora!", type="primary", use_container_width=True):
                if iniciar_partida_sincrona(batalha_id, time_inicial["id"]):
                    st.success("🚀 Partida iniciada com sucesso! Desbloqueando telas...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Falha ao atualizar o status da partida no Supabase.")
        
        st.markdown("---")

    # ------------------------------------------------------------------------
    # ⏳ LOBBY DE ESPERA PARA O ALUNO 
    # ------------------------------------------------------------------------
    if tipo_usuario == "aluno" and str(batalha.get("status")).lower() == "agendada":
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("⏳ **Sala de Espera:** A partida ainda não foi iniciada pelo professor. Aguarde no lobby, esta página vai atualizar sozinha assim que o cronômetro começar!")
        if st.button("⬅️ Sair da Sala", use_container_width=True):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    # Resolve identidades locais para andamento do fluxo síncrono
    if tipo_usuario == "aluno":
        time_id, time_nome = obter_time_do_usuario(usuario_id)
        
        # 🛡️ PROTEÇÃO: Se o time do aluno não for o Time A nem o Time B, ele entra como Espectador
        if str(time_id) != str(batalha.get("time_a_id")) and str(time_id) != str(batalha.get("time_b_id")):
            st.warning("👁️ Modo Espectador: A sua equipe não está escalada para disputar esta partida específica.")
            st.caption("Acompanhe o andamento e o placar das rodadas abaixo em tempo real.")
            eh_espectador = True
        else:
            eh_espectador = False
    else:
        time_id, time_nome = "PROFESSOR_CONSOLA", "Painel Docente"
        eh_espectador = False

    # Define dinamicamente quem é o rival para a mecânica do rebate
    if str(time_id) == str(batalha.get("time_a_id")):
        time_adversario_id = batalha.get("time_b_id")
    else:
        time_adversario_id = batalha.get("time_a_id")

    time_da_vez_id = batalha.get("time_da_vez_id")
    status_sincrono = batalha.get("status_sincrono", "aguardando_resposta")
    pergunta_ordem = batalha.get("pergunta_atual_ordem", 1)
    
    tentativa_atual = 2 if status_sincrono == "rebate_ativo" else 1
    eh_a_vez_deste_time = (str(time_id) == str(time_da_vez_id)) or (tipo_usuario in ("professor", "admin"))

    st.markdown(f"### 📍 Pergunta Atual: N° {pergunta_ordem}")
    
    # Renderização dinâmica dos cartões de turno
    if tipo_usuario == "aluno" and not eh_espectador:
        if eh_a_vez_deste_time:
            st.markdown(f"""
            <div style="background-color: #065f46; border-left: 6px solid #10b981; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="color: #a7f3d0; margin: 0;">🟢 É A VEZ DO SEU TIME! ({time_nome})</h4>
                <p style="color: #a7f3d0; margin: 5px 0 0 0; font-size: 14px;">
                    Tentativa: <strong>{tentativa_atual}ª Chance</strong> {"(REBATE ATIVADO! O adversário errou!)" if tentativa_atual == 2 else ""}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            nome_time_vez = batalha.get("times", {}).get("nome", "Outra equipe") if batalha.get("times") else "Adversário"
            st.markdown(f"""
            <div style="background-color: #7c2d12; border-left: 6px solid #ea580c; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="color: #ffedd5; margin: 0;">⏱️ AGUARDANDO ADVERSÁRIO...</h4>
                <p style="color: #ffedd5; margin: 5px 0 0 0; font-size: 14px;">
                    O time <strong>{nome_time_vez}</strong> está com o controle da resposta no momento.
                </p>
            </div>
            """, unsafe_allow_html=True)

    dados_pergunta = obter_pergunta_atual(batalha_id, pergunta_ordem)
    
    if not dados_pergunta:
        st.info("🏁 Não há mais perguntas cadastradas para esta batalha ou aguardando liberação do professor.")
        if st.button("Voltar ao Menu Principal", use_container_width=True):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    with st.container(border=True):
        st.markdown(f"**Enunciado:**\n{dados_pergunta['enunciado']}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Selecione a alternativa correta:**")
    
    # Constrói os botões interativos desativando-os se for espectador ou não for a vez do time
    for alt in dados_pergunta["alternativas"]:
        letra_ordem = chr(64 + int(alt["ordem"]))
        texto_opcao = f"{letra_ordem}) {alt['texto']}"
        
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
                st.toast("🎉 Incrível! Seu time acertou e faturou o ponto!", icon="🔥")
            elif resultado == "rebate":
                st.toast("❌ Errado! A pergunta foi passada para o adversário no modo Rebate.", icon="⚠️")
            elif resultado == "ambos_erraram":
                st.toast("🛑 Ambos os times erraram esta questão. Passando para a próxima...", icon="💀")
                
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Sair da Partida (Voltar para Arena)", type="secondary", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()