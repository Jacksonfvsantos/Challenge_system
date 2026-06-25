import streamlit as st
import time
from database.conexao import supabase
from services.batalha_service import encerrar_partida_sincrona, processar_resposta_sincrona
from utils.estilo import aplicar_estilo, cabecalho

# --- FUNÇÕES DE SUPORTE AO BACKEND DA RODADA ---

def obter_estado_batalha(batalha_id):
    try:
        res = supabase.table("batalhas").select("*").eq("id", batalha_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"❌ Erro [obter_estado_batalha]: {e}")
        return None

def obter_nomes_dos_times(time_a_id, time_b_id):
    try:
        res = supabase.table("times").select("id, nome").in_("id", [time_a_id, time_b_id]).execute()
        mapeamento = {str(t["id"]).strip(): t["nome"] for t in res.data} if res.data else {}
        return mapeamento.get(str(time_a_id).strip(), "Time A"), mapeamento.get(str(time_b_id).strip(), "Time B")
    except Exception:
        return "Time A", "Time B"

def obter_pergunta_atual(batalha_id, ordem_pergunta):
    try:
        vinculo = (
            supabase
            .table("batalha_perguntas")
            .select("questao_id")
            .eq("batalha_id", batalha_id)
            .eq("ordem", int(ordem_pergunta))
            .execute()
        )
        if not vinculo.data:
            return None
            
        q_id = str(vinculo.data[0]["questao_id"]).strip()
        questao = supabase.table("questoes").select("*").eq("id", q_id).execute()
        if not questao.data:
            return None
            
        dados_questao = questao.data[0]
        indice_correto_banco = int(dados_questao.get("indice_correto", 0))
        
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

def calcular_placar_atual(batalha_id, time_a_id, time_b_id):
    try:
        res = supabase.table("batalha_respostas").select("time_id, resposta_correta").eq("batalha_id", batalha_id).execute()
        pontos_a, pontos_b = 0, 0
        if res.data:
            for resp in res.data:
                if resp.get("resposta_correta") is True:
                    if str(resp.get("time_id")).strip() == str(time_a_id).strip():
                        pontos_a += 1
                    elif str(resp.get("time_id")).strip() == str(time_b_id).strip():
                        pontos_b += 1
        return pontos_a, pontos_b
    except Exception:
        return 0, 0


# --- 🔄 1. COMPONENTE REATIVO DE ATUALIZAÇÃO DO PLACAR ---
@st.fragment(run_every=3)
def painel_estatistico_reativo(batalha_id, time_a_id, time_b_id, nome_time_a, nome_time_b, dados_pergunta, ordem_renderizada_atualmente):
    batalha_live = obter_estado_batalha(batalha_id)
    if batalha_live:
        ordem_banco = int(batalha_live.get("pergunta_atual_ordem", 1))
        # Se detetar no banco que a pergunta mudou, ativa a flag para atualizar a tela estrutural externa
        if ordem_banco != int(ordem_renderizada_atualmente):
            st.session_state["forcar_refresh_pergunta"] = True
            st.rerun()

    pontos_a, pontos_b = calcular_placar_atual(batalha_id, time_a_id, time_b_id)
    
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px; border: 1px solid #334155;">
        <span style="color: #94a3b8; font-size: 14px; font-weight: bold;">📊 PLACAR DA ARENA</span><br>
        <span style="color: #38bdf8; font-size: 18px; font-weight: bold;">{nome_time_a}: {pontos_a} XP</span> 
        <span style="color: #64748b; font-size: 18px;"> vs </span> 
        <span style="color: #fb923c; font-size: 18px; font-weight: bold;">{nome_time_b}: {pontos_b} XP</span>
    </div>
    """, unsafe_allow_html=True)

    if dados_pergunta:
        try:
            res_respostas = supabase.table("batalha_respostas").select("*").eq("batalha_id", batalha_id).eq("questao_id", dados_pergunta["id"]).execute()
            historico = res_respostas.data or []
        except Exception:
            historico = []

        if historico:
            st.markdown("##### 📢 Registro de Submissões do Round:")
            for item in historico:
                id_time_respondido = str(item.get("time_id")).strip()
                nome_do_respondente = nome_time_a if id_time_respondido == time_a_id else nome_time_b
                chance = item.get("tentativa_numero", 1)
                
                # Voltamos para a exibição estável (apenas informativo de acerto/erro)
                if item.get("resposta_correta") is True:
                    st.success(f"🎯 **{nome_do_respondente}** RESPONDEU e ACERTOU na {chance}ª tentativa!")
                else:
                    st.error(f"❌ **{nome_do_respondente}** RESPONDEU e ERROU na {chance}ª tentativa!")
            st.markdown("---")


# --- 🖥️ 2. INTERFACE E ROTEADOR ESTRUTURAL ---
def tela_batalha_rodada():
    aplicar_estilo()
    
    # Executa o refresh da tela estrutural se o fragmento em background deu sinal de nova pergunta
    if st.session_state.get("forcar_refresh_pergunta", False):
        st.session_state["forcar_refresh_pergunta"] = False
        st.rerun()

    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    if tipo_usuario == "aluno":
        time_id, time_nome = obter_time_do_usuario(usuario_id)
        if not time_id:
            st.error("🛑 Você precisa estar vinculado a uma equipe para acessar esta sala!")
            return
    else:
        time_id, time_nome = "PROFESSOR_CONSOLA", "Painel Docente"
    
    if "batalha_ativa_id" not in st.session_state:
        st.warning("Nenhuma batalha ativa selecionada.")
        return

    batalha_id = st.session_state.batalha_ativa_id
    batalha = obter_estado_batalha(batalha_id)
    
    if not batalha:
        st.warning("Batalha não localizada.")
        return

    time_a_id = str(batalha.get("time_a_id")).strip()
    time_b_id = str(batalha.get("time_b_id")).strip()
    nome_time_a, nome_time_b = obter_nomes_dos_times(time_a_id, time_b_id)
    
    pergunta_ordem = int(batalha.get("pergunta_atual_ordem", 1))
    dados_pergunta = obter_pergunta_atual(batalha_id, pergunta_ordem)

    painel_estatistico_reativo(batalha_id, time_a_id, time_b_id, nome_time_a, nome_time_b, dados_pergunta, pergunta_ordem)

    # --- VERIFICAÇÃO DE CONCLUSÃO DO JOGO ---
    if batalha.get("finalizada") is True or str(batalha.get("status")).lower() == "finalizada" or not dados_pergunta:
        if not batalha.get("finalizada"):
            encerrar_partida_sincrona(batalha_id)
            
        st.success("🏁 **A batalha foi encerrada oficialmente! Todas as perguntas foram respondidas.**")
        pontos_a, pontos_b = calcular_placar_atual(batalha_id, time_a_id, time_b_id)
        
        if pontos_a > pontos_b:
            st.markdown(f"### 🏆 Vencedor da Arena: **{nome_time_a}** (Placar: {pontos_a} vs {pontos_b})")
        elif pontos_b > pontos_a:
            st.markdown(f"### 🏆 Vencedor da Arena: **{nome_time_b}** (Placar: {pontos_b} vs {pontos_a})")
        else:
            st.markdown(f"### 🤝 Fim de Confronto: **Empate Técnico!** (Placar: {pontos_a} vs {pontos_b})")
            
        if st.button("Voltar para a Arena de Equipes", use_container_width=True, key="btn_batalha_fim"):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    # Controles iniciais do professor na sala de espera
    if tipo_usuario in ("professor", "admin") and str(batalha.get("status")).lower() == "agendada":
        st.markdown("### 🎛️ Painel de Controle de Início da Partida")
        try:
            res_times = supabase.table("times").select("id, nome").in_("id", [time_a_id, time_b_id]).execute()
            lista_times_sala = res_times.data or []
        except Exception:
            lista_times_sala = []
            
        if not lista_times_sala:
            st.error("🛑 Erro relacional: As equipes selecionadas não existem no banco.")
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

    # Gerenciamento de Visibilidade e Modo Espectador
    eh_espectador = False
    if tipo_usuario == "aluno":
        if str(time_id) != time_a_id and str(time_id) != time_b_id:
            st.warning("👁️ Modo Espectador ativo. Acompanhe os rounds na tela.")
            eh_espectador = True
    else:
        eh_espectador = True

    time_adversario_id = time_b_id if str(time_id) == time_a_id else time_a_id
    time_da_vez_id = str(batalha.get("time_da_vez_id")).strip() if batalha.get("time_da_vez_id") else ""
    status_sincrono = batalha.get("status_sincrono", "aguardando_resposta")
    
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
                # ✅ CORRIGIDO: Enviando exatamente os 6 argumentos esperados pelo batalha_service.py original!
                res = processar_resposta_sincrona(
                    batalha_id, dados_pergunta["id"], time_id,
                    alt["correta"], time_adversario_id, tentativa_atual
                )
                time.sleep(0.5)
                st.rerun()

    st.markdown("<br><hr style='border-color: #334155;'>", unsafe_allow_html=True)
    if st.button("🚪 Sair da Sala / Voltar para a Arena", use_container_width=True, type="secondary", key="btn_sair_sala_emergencia"):
        if "batalha_ativa_id" in st.session_state:
            del st.session_state["batalha_ativa_id"]
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()