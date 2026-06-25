import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import encerrar_partida_sincrona

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
        # 1. Busca flexível: tenta localizar o round primeiro como tipo Inteiro
        vinculo = (
            supabase
            .table("batalha_perguntas")
            .select("questao_id")
            .eq("batalha_id", batalha_id)
            .eq("ordem", int(ordem_pergunta))
            .execute()
        )
        
        # Se falhar, tenta localizar passando o round como String pura
        if not vinculo.data:
            vinculo = (
                supabase
                .table("batalha_perguntas")
                .select("questao_id")
                .eq("batalha_id", batalha_id)
                .eq("ordem", str(ordem_pergunta))
                .execute()
            )
            
        if not vinculo.data:
            return None
            
        q_id = str(vinculo.data[0]["questao_id"]).strip()
        
        # 2. Busca o enunciado e configurações na tabela 'questoes'
        questao = supabase.table("questoes").select("*").eq("id", q_id).execute()
        if not questao.data:
            return None
            
        dados_questao = questao.data[0]
        indice_correto_banco = int(dados_questao.get("indice_correto", 0))
        
        # 3. Busca alternativas associadas na tabela 'alternativas'
        alternativas = supabase.table("alternativas").select("*").eq("questao_id", q_id).order("ordem").execute()
        lista_alt_data = alternativas.data or []
        
        alternativas_formatadas = []
        for alt in lista_alt_data:
            eh_correta = alt.get("correta") if alt.get("correta") is not None else (int(alt["ordem"]) == (indice_correto_banco + 1))
            
            alternativas_formatadas.append({
                "id": alt["id"],
                "texto": alt["texto"],
                "ordem": alt["ordem"],
                "correta": eh_correta
            })
        
        return {
            "id": q_id,
            "enunciado": dados_questao.get("enunciado", "Questão sem enunciado"),
            "alternativas": alternativas_formatadas
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


# --- 🔄 COMPONENTE REATIVO AUTO-REFRESH ---
@st.fragment(run_every=3)
def renderizar_conteudo_dinamico_sala(batalha_id, usuario_id, tipo_usuario, time_id, time_nome):
    batalha = obter_estado_batalha(batalha_id)
    
    if not batalha or batalha.get("finalizada") is True or str(batalha.get("status")).lower() == "finalizada":
        st.balloons()
        st.success("🎉 A batalha foi encerrada oficialmente!")
        if st.button("Voltar para a Arena", use_container_width=True, key="btn_batalha_fim"):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    # Painel de controle inicial exclusivo do docente
    if tipo_usuario in ("professor", "admin") and str(batalha.get("status")).lower() == "agendada":
        st.markdown("### 🎛️ Painel de Controle de Início da Partida")
        st.info("Selecione qual equipe começará atacando na rodada ao vivo:")
        
        time_a_id = str(batalha.get("time_a_id")).strip()
        time_b_id = str(batalha.get("time_b_id")).strip()
        
        try:
            res_times = supabase.table("times").select("id, nome").in_("id", [time_a_id, time_b_id]).execute()
            lista_times_sala = res_times.data or []
        except Exception:
            lista_times_sala = []
            
        if not lista_times_sala:
            st.error("🛑 Erro relacional: As equipes selecionadas não existem no banco de dados.")
        else:
            time_inicial = st.selectbox("Quem joga primeiro?", options=lista_times_sala, format_func=lambda x: str(x["nome"]).strip())
            
            from services.batalha_service import iniciar_partida_sincrona
            if st.button("🔥 Começar Partida Agora!", type="primary", use_container_width=True):
                if iniciar_partida_sincrona(batalha_id, time_inicial["id"]):
                    st.success("🚀 Partida iniciada!")
                    st.rerun()
        return

    if tipo_usuario == "aluno" and str(batalha.get("status")).lower() == "agendada":
        st.info("⏳ **Sala de Espera:** Aguardando o professor dar o sinal de início. Esta tela atualizará sozinha.")
        return

    # Resolução de permissões
    eh_espectador = False
    if tipo_usuario == "aluno":
        if str(time_id) != str(batalha.get("time_a_id")).strip() and str(time_id) != str(batalha.get("time_b_id")).strip():
            st.warning("👁️ Modo Espectador ativado.")
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
                <h4 style="color: #a7f3d0; margin: 0;">🟢 SEU TIME RESPONDE AGORA! ({time_nome})</h4>
                <p style="color: #a7f3d0; margin: 5px 0 0 0; font-size: 14px;">Tentativa: {tentativa_atual}ª Chance</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #7c2d12; border-left: 6px solid #ea580c; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="color: #ffedd5; margin: 0;">⏱️ AGUARDANDO ADVERSÁRIO...</h4>
            </div>
            """, unsafe_allow_html=True)

    # Coleta a pergunta baseada na ordem lógica
    dados_pergunta = obter_pergunta_atual(batalha_id, pergunta_ordem)
    
    if not dados_pergunta:
        st.warning("🏁 Todas as perguntas desta rodada foram respondidas!")
        if tipo_usuario in ("professor", "admin"):
            if st.button("🏁 Finalizar e Arquivar Batalha", type="primary", use_container_width=True):
                if encerrar_partida_sincrona(batalha_id):
                    st.success("Batalha finalizada!")
                    time.sleep(0.5)
                    st.session_state.pagina = "batalha_de_equipes"
                    st.rerun()
        return

    with st.container(border=True):
        st.markdown(f"**Enunciado:**\n{dados_pergunta['enunciado']}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if not dados_pergunta["alternativas"]:
        st.warning("⚠️ Esta questão não possui opções vinculadas.")
    else:
        for alt in dados_pergunta["alternativas"]:
            letra = chr(64 + int(alt["ordem"]))
            texto_opcao = f"{letra}) {alt['texto']}"
            
            pode_clicar = eh_a_vez_deste_time and (not eh_espectador)
            
            if st.button(texto_opcao, key=f"btn_alt_{alt['id']}", use_container_width=True, disabled=not pode_clicar):
                res = processar_resposta_sincrona(
                    batalha_id, dados_pergunta["id"], time_id, 
                    alt["correta"], time_adversario_id, tentativa_atual
                )
                time.sleep(0.5)
                st.rerun()


# --- ROTEADOR PRINCIPAL ---
def tela_batalha_rodada():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    if tipo_usuario == "aluno":
        time_id, time_nome = obter_time_do_usuario(usuario_id)
        if not time_id:
            st.error("🛑 Você precisa estar em um time para participar!")
            return
    else:
        time_id, time_nome = "PROFESSOR_CONSOLA", "Painel Docente"
    
    if "batalha_ativa_id" not in st.session_state:
        st.warning("Nenhuma batalha selecionada.")
        return

    batalha_id = st.session_state.batalha_ativa_id
    renderizar_conteudo_dinamico_sala(batalha_id, usuario_id, tipo_usuario, time_id, time_nome)