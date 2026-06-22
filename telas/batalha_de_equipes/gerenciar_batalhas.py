import streamlit as st
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import iniciar_partida_sincrona, liberar_proxima_pergunta

def obter_batalha_detalhada(batalha_id):
    try:
        res = supabase.table("batalhas").select("*").eq("id", batalha_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def tela_batalha_gerenciar():
    aplicar_estilo()
    cabecalho("🛠️ Console de Controle Síncrono", "Área exclusiva do docente para orquestrar as rodadas ao vivo")

    # 1. Recupera a batalha selecionada na tela anterior
    batalha_id = st.session_state.get("batalha_ativa_id")
    if not batalha_id:
        st.warning("Nenhuma batalha foi selecionada para gerenciamento.")
        if st.button("⬅️ Voltar para a Arena"):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    b = obter_batalha_detalhada(batalha_id)
    if not b:
        st.error("Erro ao carregar dados da partida.")
        return

    st.markdown(f"### 📋 Partida: {b['titulo']}")
    st.write(f"**Descrição:** {b.get('descricao', 'Sem descrição.')}")
    st.write(f"**Modo de Jogo:** {str(b.get('modalidade', '')).upper()}")
    st.divider()

    # Puxa os times cadastrados para o professor decidir quem começa jogando
    try:
        times_res = supabase.table("times").select("id, nome").execute()
        listagem_times = times_res.data or []
    except Exception:
        listagem_times = []

    # ========================================================================
    # ESTADO 1: PARTIDA AGENDADA (PRONTOS PARA O START)
    # ========================================================================
    if b["status"] == "agendada":
        st.info("🎯 Esta batalha síncrona ainda não começou. Prepare a sala de aula antes de dar o Start.")
        
        if not listagem_times:
            st.error("❌ Não existem equipes cadastradas no sistema. Cadastre os times antes de iniciar.")
            return

        # Formulário rápido de setup inicial
        with st.container(border=True):
            st.markdown("#### ⚙️ Configuração de Inicialização")
            time_inicial = st.selectbox(
                "Qual equipe começará respondendo a 1ª Pergunta?",
                options=listagem_times,
                format_func=lambda x: x["nome"]
            )
            
            if st.button("🚀 Iniciar Partida Ao Vivo (Liberar Telas)", type="primary", use_container_width=True):
                if iniciar_partida_sincrona(batalha_id, time_inicial["id"]):
                    st.success("⚔️ Batalha iniciada! As telas dos alunos foram desbloqueadas automaticamente.")
                    st.rerun()
                else:
                    st.error("Falha ao comunicar início com o Supabase.")

    # ========================================================================
    # ESTADO 2: PARTIDA EM ANDAMENTO (CONTROLE DE ROUNDS)
    # ========================================================================
    elif b["status"] == "em_andamento":
        st.success("🟢 A PARTIDA ESTÁ ACONTECENDO AGORA")
        
        # Painel de Telemetria (O que está gravado no banco neste milissegundo)
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Rodada / Pergunta Atual", f"N° {b['pergunta_atual_ordem']}")
        with col_r2:
            status_cor = "🔴 Rebate" if b["status_sincrono"] == "rebate_ativo" else "🟢 Regular"
            st.metric("Status do Turno", status_cor)
        with col_r3:
            # Busca o nome do time da vez
            nome_da_vez = "Indeterminado"
            if b["time_da_vez_id"]:
                match_time = next((t for t in listagem_times if str(t["id"]) == str(b["time_da_vez_id"])), None)
                if match_time: nome_da_vez = match_time["nome"]
            st.metric("Equipe Jogando", nome_da_vez)

        st.divider()
        st.markdown("#### 🎮 Painel de Intervenção do Professor")
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            with st.container(border=True):
                st.markdown("**Avançar Jogo**")
                st.caption("Força o avanço para a próxima questão do banco de dados (use caso as equipes travem).")
                
                proximo_time = st.selectbox(
                    "Passar a vez para:",
                    options=listagem_times,
                    format_func=lambda x: x["nome"],
                    key="sel_next_team"
                )
                
                if st.button("⏭️ Pular para Próxima Pergunta", use_container_width=True):
                    nova_ordem = b["pergunta_atual_ordem"] + 1
                    if liberar_proxima_pergunta(batalha_id, nova_ordem, proximo_time["id"]):
                        st.toast(f"Avançado para a pergunta {nova_ordem}!", icon="🚀")
                        st.rerun()

        with col_p2:
            with st.container(border=True):
                st.markdown("**Encerrar Desafio**")
                st.caption("Fecha o fluxo de conexões desta partida, congela os scores e gera o placar final.")
                
                if st.button("🏁 Finalizar Batalha Definitivamente", type="primary", use_container_width=True):
                    try:
                        supabase.table("batalhas").update({"finalizada": True, "status": "finalizada"}).eq("id", batalha_id).execute()
                        st.success("Partida encerrada com sucesso!")
                        st.session_state.pagina = "batalha_de_equipes"
                        st.rerun()
                    except Exception:
                        st.error("Erro ao finalizar.")

        # Botão rápido de recarregamento do painel do professor
        if st.button("🔄 Atualizar Painel de Monitoramento", use_container_width=True):
            st.rerun()

    # Botão de escape seguro
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Sair do Painel de Controle", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()
