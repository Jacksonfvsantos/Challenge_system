import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

# --- FUNÇÕES DE SUPORTE AO BACKEND DA RODADA ---

def obter_estado_batalha(batalha_id):
    try:
        res = supabase.table("batalhas").select("*").eq("id", batalha_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"❌ Erro [obter_estado_batalha]: {e}")
        return None

def obter_pergunta_atual(batalha_id, ordem_pergunta):
    try:
        # 1. Busca qual questão está vinculada a este round/ordem
        vinculo = (
            supabase
            .table("batalha_perguntas")
            .select("questao_id")
            .eq("batalha_id", batalha_id)
            .eq("ordem", ordem_pergunta)
            .execute()
        )
        if not vinculo.data:
            print(f"⚠️ Nenhum vínculo encontrado para ordem {ordem_pergunta} na batalha {batalha_id}")
            return None
            
        q_id = vinculo.data[0]["questao_id"]
        
        # 2. Busca o enunciado e as alternativas vinculadas na tabela 'alternativas'
        questao = supabase.table("questoes").select("*").eq("id", q_id).execute()
        alternativas = supabase.table("alternativas").select("*").eq("questao_id", q_id).order("ordem").execute()
        
        return {
            "id": q_id,
            "enunciado": questao.data[0]["enunciado"] if questao.data else "Questão não encontrada",
            "alternativas": alternativas.data or []
        }
    except Exception as e:
        print(f"❌ Erro crítico em [obter_pergunta_atual]: {e}")
        return None

def obter_time_do_usuario(usuario_id):
    try:
        res = supabase.table("time_membros").select("time_id, times(nome)").eq("usuario_id", usuario_id).execute()
        if res.data:
            return str(res.data[0]["time_id"]).strip(), res.data[0]["times"]["nome"]
        return None, None
    except Exception as e:
        print(f"❌ Erro [obter_time_do_usuario]: {e}")
        return None, None

def processar_resposta_sincrona(batalha_id, questao_id, time_id, alternativa_correta, time_adversario_id, tentativa_atual):
    try:
        # Grava o histórico do log de respostas para auditoria/placar
        supabase.table("batalha_respostas").insert({
            "batalha_id": batalha_id,
            "questao_id": questao_id,
            "time_id": time_id,
            "resposta_correta": alternativa_correta,
            "tentativa_numero": tentativa_atual
        }).execute()

        batalha = obter_estado_batalha(batalha_id)
        proxima_ordem = int(batalha["pergunta_atual_ordem"]) + 1

        if alternativa_correta:
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": proxima_ordem,
                "status_sincrono": "aguardando_resposta",
                "time_da_vez_id": time_adversario_id
            }).eq("id", batalha_id).execute()
            return "acertou"
        else:
            if int(tentativa_atual) == 1:
                supabase.table("batalhas").update({
                    "status_sincrono": "rebate_ativo",
                    "time_da_vez_id": time_adversario_id
                }).eq("id", batalha_id).execute()
                return "rebate"
            else:
                supabase.table("batalhas").update({
                    "pergunta_atual_ordem": proxima_ordem,
                    "status_sincrono": "aguardando_resposta",
                    "time_da_vez_id": time_id
                }).eq("id", batalha_id).execute()
                return "ambos_erraram"
    except Exception as e:
        print(f"❌ Erro [processar_resposta_sincrona]: {e}")
        return "erro"


# --- 🔄 FRAGMENTO AUTO-REFRESH SÍNCRONO (POLLING SEGURO) ---
@st.fragment(run_every=3)
def renderizar_conteudo_dinamico_sala(batalha_id, usuario_id, tipo_usuario, time_id, time_nome):
    batalha = obter_estado_batalha(batalha_id)
    
    if not batalha or batalha.get("finalizada") is True or str(batalha.get("status")).lower() == "finalizada":
        st.success("🎉 A batalha foi encerrada! Verifique o placar final com o professor.")
        if st.button("Voltar para a Arena", use_container_width=True):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    # --- CONTROLADOR DO PROFESSOR (LOBBY DE ENTRADA) ---
    if tipo_usuario in ("professor", "admin") and str(batalha.get("status")).lower() == "agendada":
        st.markdown("### 🎛️ Painel de Controle de Início da Partida")
        st.info("Escolha qual das duas equipes iniciará atacando para libertar os botões dos alunos:")
        
        time_a_id = str(batalha.get("time_a_id")).strip()
        time_b_id = str(batalha.get("time_b_id")).strip()
        
        try:
            res_times = supabase.table("times").select("id, nome").in_("id", [time_a_id, time_b_id]).execute()
            lista_times_sala = res_times.data or []
        except Exception:
            lista_times_sala = []
            
        if not lista_times_sala:
            st.error("🛑 Erro: As duas equipes escaladas não foram encontradas no banco de dados.")
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
                    st.success("🚀 Partida iniciada com sucesso!")
                    st.rerun()
        return

    # --- LOBBY DE ESPERA DO ESTUDANTE ---
    if tipo_usuario == "aluno" and str(batalha.get("status")).lower() == "agendada":
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("⏳ **Sala de Espera:** A partida ainda não foi iniciada pelo professor. Aguarde neste lobby, esta seção vai ativar-se automaticamente assim que o jogo começar!")
        return

    # --- RESOLUÇÃO DE PERMISSÕES E PAPÉIS ---
    eh_espectador = False
    if tipo_usuario == "aluno":
        if str(time_id) != str(batalha.get("time_a_id")).strip() and str(time_id) != str(batalha.get("time_b_id")).strip():
            st.warning("👁️ Modo Espectador: A sua equipe não está escalada para esta disputa.")
            eh_espectador = True
    else:
        eh_espectador = True

    if str(time_id) == str(batalha.get("time_a_id")).strip():
        time_adversario_id = str(batalha.get("time_b_id")).strip()
    else:
        time_adversario_id = str(batalha.get("time_a_id")).strip()
    
    time_da_vez_id = str(batalha.get("time_da_vez_id")).strip() if batalha.get("time_da_vez_id") else ""
    status_sincrono = batalha.get("status_sincrono", "aguardando_resposta")
    pergunta_ordem = int(batalha.get("pergunta_atual_ordem", 1))
    
    tentativa_atual = 2 if status_sincrono == "rebate_ativo" else 1
    eh_a_vez_deste_time = (str(time_id).strip() == time_da_vez_id)

    st.markdown(f"### 📍 Pergunta Atual: N° {pergunta_ordem}")
    
    if tipo_usuario == "aluno" and not eh_espectador:
        if eh_a_vez_deste_time:
            st.markdown(f"""
            <div style="background-color: #065f46; border-left: 6px solid #10b981; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="color: #a7f3d0; margin: 0;">🟢 É A VEZ DO SEU TIME! ({time_nome})</h4>
                <p style="color: #a7f3d0; margin: 5px 0 0 0; font-size: 14px;">
                    Sua equipe está com o controle. Tentativa: <strong>{tentativa_atual}ª Chance</strong> {"(REBATE ATIVADO!)" if tentativa_atual == 2 else ""}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #7c2d12; border-left: 6px solid #ea580c; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="color: #ffedd5; margin: 0;">⏱️ AGUARDANDO ADVERSÁRIO...</h4>
                <p style="color: #ffedd5; margin: 5px 0 0 0; font-size: 14px;">
                    A outra equipe está respondendo a questão neste momento.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # --- BUSCA DA QUESTÃO COM SUA RESPECTIVA COLA DE ALTERNATIVAS ---
    dados_pergunta = obter_pergunta_atual(batalha_id, pergunta_ordem)
    
    if not dados_pergunta:
        st.info("🏁 Parabéns! Chegamos ao fim das perguntas preparadas para esta rodada.")
        return

    with st.container(border=True):
        st.markdown(f"**Enunciado:**\n{dados_pergunta['enunciado']}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Selecione a alternativa correta:**")
    
    if not dados_pergunta["alternativas"]:
        st.warning("⚠️ Atenção: Esta questão não possui opções cadastradas na tabela 'alternativas' vinculadas ao seu ID.")
    else:
        # Loop estruturado de renderização das alternativas (A, B, C, D)
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
                    st.toast("🎉 Excelente! Sua equipe acertou e garantiu o ponto!", icon="🔥")
                elif resultado == "rebate":
                    st.toast("❌ Errado! O Rebate foi ativado. A bola passou para o adversário!", icon="⚠️")
                elif resultado == "ambos_erraram":
                    st.toast("🛑 Ambos falharam nesta questão. Avançando de round...", icon="💀")
                    
                time.sleep(0.5)
                st.rerun()


# --- INTERFACE VISUAL PRINCIPAL STREAMLIT ---

def tela_batalha_rodada():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    if tipo_usuario == "aluno":
        time_id, time_nome = obter_time_do_usuario(usuario_id)
        if not time_id:
            st.error("🛑 Acesso Negado: Precisa de fazer parte de uma equipe para entrar na partida síncrona!")
            if st.button("🏢 Criar minha Equipe Agora", type="primary", use_container_width=True):
                st.session_state.pagina = "batalha_times"
                st.rerun()
            return
    else:
        time_id, time_nome = "PROFESSOR_CONSOLA", "Painel Docente"
    
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
    
    try:
        b_tit = supabase.table("batalhas").select("titulo").eq("id", batalha_id).execute()
        titulo_sala = b_tit.data[0]["titulo"] if b_tit.data else "Partida Síncrona"
    except Exception:
        titulo_sala = "Partida Síncrona"

    cabecalho(f"⚔️ {titulo_sala}", "Arena Síncrona ao Vivo — Modo Bate-Rebate")
    
    # Aciona o fragmento reativo e isolado
    renderizar_conteudo_dinamico_sala(batalha_id, usuario_id, tipo_usuario, time_id, time_nome)

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Sair da Sala (Voltar para Arena)", type="secondary", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()