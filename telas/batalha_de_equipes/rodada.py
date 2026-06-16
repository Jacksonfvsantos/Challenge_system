import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

# --- FUNÇÕES DE SUPORTE AO BACKEND DA RODADA ---

def obter_estado_batalha(batalha_id):
    """Busca o estado síncrono atual da batalha diretamente no banco."""
    try:
        res = supabase.table("batalhas").select("*, times(nome)").eq("id", batalha_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def obter_pergunta_atual(batalha_id, ordem_pergunta):
    """Busca a questão ativa mapeada para esta rodada da batalha."""
    try:
        # Busca o vínculo na tabela intermediária
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
        
        # Busca o enunciado e alternativas da questão
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
    """Descobre o ID e o nome do time ao qual o aluno logado pertence."""
    try:
        res = supabase.table("time_membros").select("time_id, times(nome)").eq("usuario_id", usuario_id).execute()
        if res.data:
            return res.data[0]["time_id"], res.data[0]["times"]["nome"]
        return None, None
    except Exception:
        return None, None

def processar_resposta_sincrona(batalha_id, questao_id, time_id, alternativa_correta, time_adversario_id, tentativa_atual):
    """Aplica a regra de negócio do Bate-Rebate no banco de dados."""
    try:
        # 1. Registra a tentativa do time na tabela de respostas
        supabase.table("batalha_respostas").insert({
            "batalha_id": batalha_id,
            "questao_id": questao_id,
            "time_id": time_id,
            "resposta_correta": alternativa_correta,
            "tentativa_numero": tentativa_atual
        }).execute()

        if alternativa_correta:
            # ACERTOU: Avança para a próxima pergunta e zera o status para a nova rodada
            batalha = obter_estado_batalha(batalha_id)
            proxima_ordem = batalha["pergunta_atual_ordem"] + 1
            
            supabase.table("batalhas").update({
                "pergunta_atual_ordem": proxima_ordem,
                "status_sincrono": "aguardando_resposta",
                "time_da_vez_id": time_adversario_id # Passa o início da próxima para o outro time equilibrar
            }).eq("id", batalha_id).execute()
            return "acertou"
        else:
            # ERROU: Verifica se foi o primeiro erro (concede o Rebate) ou o segundo erro (pergunta encerrada)
            if tentativa_current == 1:
                # Passa a vez para o adversário e ativa o Rebate
                supabase.table("batalhas").update({
                    "status_sincrono": "rebate_ativo",
                    "time_da_vez_id": time_adversario_id
                }).eq("id", batalha_id).execute()
                return "rebate"
            else:
                # Ambos erraram a mesma pergunta: Avança o jogo sem pontuar ninguém
                batalha = obter_estado_batalha(batalha_id)
                proxima_ordem = batalha["pergunta_atual_ordem"] + 1
                
                supabase.table("batalhas").update({
                    "pergunta_atual_ordem": proxima_ordem,
                    "status_sincrono": "aguardando_resposta",
                    "time_da_vez_id": time_id # Mantém com quem errou por último para iniciar a próxima
                }).eq("id", batalha_id).execute()
                return "ambos_erraram"
    except Exception:
        return "erro"

# --- INTERFACE VISUAL STREAMLIT ---

def tela_batalha_rodada():
    aplicar_estilo()
    
    # Adiciona o componente de Auto-Refresh (recarrega a tela a cada 3 segundos para sincronizar)
    st.logo("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png") # Opcional
    st.caption("🔄 Sincronização automática ativa (3s)")
    time.sleep(3)
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    # Recupera ou define uma batalha ativa para testes (em produção, você passa o ID via session_state)
    if "batalha_ativa_id" not in st.session_state:
        # Busca a primeira batalha não finalizada para carregar como exemplo
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
    
    if not batalha or batalha.get("finalizada"):
        st.success("🎉 A batalha foi encerrada! Verifique o placar final com o professor.")
        if st.button("Voltar para a Arena"):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    cabecalho(f"⚔️ Partida Síncrona: {batalha['titulo']}", "Modo de Jogo atual: Bate-Rebate")

    # 1. Resolve o Time do Jogador e o Adversário
    time_id, time_nome = obter_time_do_usuario(usuario_id)
    
    # Para o painel funcionar, precisamos descobrir quem é o time adversário
    try:
        todos_times = supabase.table("times").select("id, nome").execute()
        adversarios = [t for t in todos_times.data if str(t["id"]) != str(time_id)]
        time_adversario_id = adversarios[0]["id"] if adversarios else None
        time_adversario_nome = adversarios[0]["name"] if adversarios else "Adversário"
    except Exception:
        time_adversario_id = None
        time_adversario_nome = "Adversário"

    # 2. Painel de Status de Turno (Quem joga agora?)
    time_da_vez_id = batalha.get("time_da_vez_id")
    status_sincrono = batalha.get("status_sincrono", "aguardando_resposta")
    pergunta_ordem = batalha.get("pergunta_atual_ordem", 1)
    
    tentativa_atual = 2 if status_sincrono == "rebate_ativo" else 1

    # Define se o usuário atual tem permissão para clicar nos botões
    eh_a_vez_deste_time = (str(time_id) == str(time_da_vez_id))

    st.markdown(f"### 📍 Pergunta Atual: N° {pergunta_ordem}")
    
    # Layout visual de alerta de Turno
    if eh_a_vez_deste_time:
        st.markdown(f"""
        <div style="background-color: #d4edda; border-left: 6px solid #28a745; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h4 style="color: #155724; margin: 0;">🟢 É A VEZ DO SEU TIME! ({time_nome})</h4>
            <p style="color: #155724; margin: 5px 0 0 0; font-size: 14px;">
                Tentativa: <strong>{tentativa_atual}ª Chance</strong> {"(REBATE ATIVADO! O adversário errou!)" if tentativa_atual == 2 else ""}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        nome_time_vez = batalha.get("times", {}).get("nome", "Outra equipe") if batalha.get("times") else "Adversário"
        st.markdown(f"""
        <div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h4 style="color: #856404; margin: 0;">⏱️ AGUARDANDO ADVERSÁRIO...</h4>
            <p style="color: #856404; margin: 5px 0 0 0; font-size: 14px;">
                O time <strong>{nome_time_vez}</strong> está com o controle da resposta no momento.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # 3. Carrega e exibe os dados da pergunta ativa
    dados_pergunta = obter_pergunta_atual(batalha_id, pergunta_ordem)
    
    if not dados_pergunta:
        st.info("🏁 Não há mais perguntas cadastradas para esta batalha ou aguardando liberação do professor.")
        if st.button("Voltar ao Menu Principal"):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    # Exibe o enunciado em destaque
    with st.container(border=True):
        st.markdown(f"**Enunciado:**\n{dados_pergunta['enunciado']}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 4. Renderiza as alternativas travando ou liberando os botões com base no Turno
    st.markdown("**Selecione a alternativa correta:**")
    
    for alt in dados_pergunta["alternativas"]:
        letra_ordem = chr(64 + int(alt["ordem"])) # Converte 1 para A, 2 para B...
        texto_opcao = f"{letra_ordem}) {alt['texto']}"
        
        # O parâmetro 'disabled' desativa o botão na hora se não for a vez do time do aluno
        if st.button(texto_opcao, key=f"alt_{alt['id']}", use_container_width=True, disabled=not eh_a_vez_deste_time):
            # Se clicou, processa o resultado imediatamente
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

    # Botão de escape seguro para o painel
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Sair da Partida (Voltar para Arena)", type="secondary", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()