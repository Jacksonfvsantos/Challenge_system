import streamlit as st
import datetime
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import encerrar_partida_sincrona, deletar_batalha

# --- FUNÇÕES DE SUPORTE AO BACKEND DAS BATALHAS ---

def listar_batalhas_por_modalidade(modalidade):
    """Busca do Supabase as batalhas ativas filtradas por síncrona ou assíncrona."""
    try:
        res = supabase.table("batalhas")\
            .select("*, times:time_da_vez_id(nome)")\
            .eq("modalidade", modalidade)\
            .eq("finalizada", False)\
            .order("created_at")\
            .execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Erro ao listar batalhas ({modalidade}): {e}")
        return []

# --- INTERFACE VISUAL PRINCIPAL ---

def tela_batalha_de_equipes():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho(
        "⚔️ Arena de Batalha de Equipes",
        "Participe de rodadas síncronas de Bate-Rebate ou resolva desafios complexos com prazo estendido"
    )

    # ------------------------------------------------------------------------
    # PAINEL SUPERIOR: DIRETRIZES E CENTRAL DE REGRAS
    # ------------------------------------------------------------------------
    col_Painel, col_Manual = st.columns([2, 1])
    
    with col_Painel:
        st.markdown("""
        **Bem-vindo à Arena de Competições!** Aqui o conhecimento técnico se transforma em pontuação de liderança. Alinhe a estratégia com seu time, 
        monitore os turnos nas rodadas ao vivo ou gerencie as entregas dos desafios de arquitetura.
        """)
        
    with col_Manual:
        with st.container(border=True):
            st.markdown("<p style='margin:0; font-weight:bold; font-size:13px;'>🛡️ Regulamento Geral</p>", unsafe_allow_html=True)
            st.caption("Confira as diretrizes de compliance, conduta e critérios de Fair Play da banca.")
            if st.button("📖 Ler Regras da Arena", use_container_width=True, key="btn_arena_regras_global"):
                st.session_state.pagina = "regras_plataforma"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # SEPARAÇÃO ARQUITETURAL: ABAS DE MODALIDADE DE JOGO
    # ------------------------------------------------------------------------
    aba_sincrona, aba_assincrona = st.tabs([
        "⚡ Arena Ao Vivo (Bate-Rebate)", 
        "⏳ Desafios com Prazo (Assíncrono)"
    ])

    # ========================================================================
    # MODE 1: ECOSSISTEMA SÍNCRONO (AO VIVO)
    # ========================================================================
    with aba_sincrona:
        st.markdown("### 🎙️ Partidas em Tempo Real")
        st.caption("Estas competições exigem sincronia. O professor dita o ritmo da liberação das questões.")
        
        # Atalho para o Aluno gerenciar o seu time
        if tipo_usuario == "aluno":
            with st.container(border=True):
                st.markdown("🏢 **Precisa criar, gerenciar ou sair da sua equipe?**")
                if st.button("Ir para Central de Equipes", use_container_width=True, key="btn_atalho_central_times"):
                    st.session_state.pagina = "batalha_times"
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
        
        batalhas_sincronas = listar_batalhas_por_modalidade("sincrona")
        
        if not batalhas_sincronas:
            st.info("Não há nenhuma batalha síncrona ativa ou agendada para este momento.")
        else:
            for bs in batalhas_sincronas:
                with st.container(border=True):
                    col_info, col_action = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"#### ⚔️ {bs['titulo']}")
                        st.write(bs.get("descricao", "Sem descrição informada."))
                        
                        if bs.get("status") == "em_andamento":
                            time_vez = bs.get("times", {}).get("nome", "Aguardando...") if bs.get("times") else "Determinar"
                            st.markdown(f"🟢 **Status:** `EM ANDAMENTO` | ⏱️ **Vez do Time:** `{time_vez}`")
                        else:
                            st.markdown("🟡 **Status:** `AGENDADA / AGUARDANDO INÍCIO`")
                            
                    with col_action:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Entrar na Sala", key=f"join_{bs['id']}", type="primary", use_container_width=True):
                            st.session_state.batalha_ativa_id = bs["id"]
                            st.session_state.pagina = "batalha_rodada"
                            st.rerun()

                        # 🔥 ADICIONADO: Controles de ciclo de vida rápidos visíveis apenas para Professores
                        if tipo_usuario in ("professor", "admin"):
                            if st.button("🛑 Encerrar", key=f"card_stop_{bs['id']}", type="secondary", use_container_width=True):
                                if encerrar_partida_sincrona(bs['id']):
                                    st.toast("Confronto finalizado e enviado para o histórico!", icon="🛑")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Erro ao encerrar partida.")

                            if st.button("🗑️ Deletar", key=f"card_del_{bs['id']}", type="secondary", use_container_width=True):
                                if deletar_batalha(bs['id']):
                                    st.toast("Batalha de testes apagada com sucesso!", icon="🗑️")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Erro ao remover do banco.")

    # ========================================================================
    # MODE 2: ECOSSISTEMA ASSÍNCRONO (PRAZOS)
    # ========================================================================
    with aba_assincrona:
        st.markdown("### 📅 Desafios e Projetos Semanais")
        st.caption("Analise os problemas de engenharia e submeta as soluções da sua equipe dentro da janela de entrega.")
        
        batalhas_assincronas = listar_batalhas_por_modalidade("assincrona")
        
        if not batalhas_assincronas:
            st.info("Nenhum desafio ou especificação assíncrona pendente de entrega.")
        else:
            agora = datetime.datetime.now(datetime.timezone.utc)
            
            for ba in batalhas_assincronas:
                prazo_str = ba.get("data_limite")
                prazo_valido = True
                
                if prazo_str:
                    try:
                        if "." in prazo_str: prazo_str = prazo_str.split(".")[0]
                        if "Z" in prazo_str: prazo_str = prazo_str.replace("Z", "+00:00")
                        prazo_dt = datetime.datetime.fromisoformat(prazo_str)
                    except ValueError:
                        prazo_valido = False
                else:
                    prazo_valido = False

                with st.container(border=True):
                    col_a_info, col_a_action = st.columns([3, 1])
                    
                    with col_a_info:
                        st.markdown(f"#### ⏳ {ba['titulo']}")
                        st.write(ba.get("descricao", "Sem diretrizes anexadas."))
                        
                        if prazo_valido:
                            exibicao_data = prazo_dt.strftime('%d/%m/%Y às %H:%M')
                            if agora > prazo_dt:
                                st.markdown(f"🛑 <span style='color:#ef4444; font-weight:bold;'>Prazo Encerrado: {exibicao_data}</span>", unsafe_allow_html=True)
                                expirada = True
                            else:
                                st.markdown(f"📅 <span style='color:#10b981; font-weight:bold;'>Entregar até: {exibicao_data}</span>", unsafe_allow_html=True)
                                expirada = False
                        else:
                            st.caption("📅 Sem prazo restritivo definido pelo docente.")
                            expirada = False

                    with col_a_action:
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_label = "Prazo Bloqueado" if expirada else "Enviar Solução"
                        if st.button(btn_label, key=f"sub_{ba['id']}", type="secondary", use_container_width=True, disabled=expirada):
                            st.session_state.batalha_ativa_id = ba["id"]
                            st.session_state.pagina = "batalha_rodada"
                            st.rerun()

    # ------------------------------------------------------------------------
    # PAINEL DE CONTROLE EXCLUSIVO (PROFESSOR / ADMIN)
    # ------------------------------------------------------------------------
    if tipo_usuario in ("professor", "admin"):
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### 🛠️ Painel Advanced de Governança Docente")
        st.caption("Ações de bastidores para provisionar equipes, ajustar integrantes e criar novos editais de competição.")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            if st.button("🏢 Gerenciar Equipes (Times)", use_container_width=True, key="btn_gov_times"):
                st.session_state.pagina = "batalha_times"
                st.rerun()
        with col_m2:
            if st.button("👥 Alocação de Alunos", use_container_width=True, key="btn_gov_members"):
                st.session_state.pagina = "batalha_integrantes"
                st.rerun()
        with col_m3:
            if st.button("📝 Abrir Nova Batalha (Híbrida)", type="primary", use_container_width=True, key="btn_gov_new_match"):
                st.session_state.pagina = "batalha_gerenciar"
                st.rerun()