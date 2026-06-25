import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import encerrar_partida_sincrona, deletar_batalha

def tela_batalha_de_equipes_principal():
    aplicar_estilo()
    cabecalho("⚔️ Arena de Competições por Equipes", "Participe de desafios síncronos ao vivo ou resolva listas com prazos estendidos")

    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()

    # Sistema de abas principais da Arena visto na imagem image_3eb045.png
    aba_ao_vivo, aba_assincrona = st.tabs(["⚡ Arena Ao Vivo (Bate-Rebate)", "⏳ Desafios com Prazo (Assíncrono)"])

    # =========================================================================
    # TAB 1: ARENA AO VIVO (SÍNCRONA)
    # =========================================================================
    with aba_ao_vivo:
        st.markdown("### 🎙️ Partidas em Tempo Real")
        st.caption("Estas competições exigem sincronia. O professor dita o ritmo da liberação das questões.")

        if tipo_usuario in ("professor", "admin"):
            if st.button("➕ Provisionar Nova Batalha", type="primary"):
                st.session_state.pagina = "batalha_gerenciar"
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

        # Busca do banco as batalhas síncronas em andamento ou agendadas
        try:
            res = (
                supabase.table("batalhas")
                .select("*, time_a:time_a_id(nome), time_b:time_b_id(nome)")
                .eq("modalidade", "sincrona")
                .eq("finalizada", False)
                .order("created_at", descending=True)
                .execute()
            )
            batalhas_ativas = res.data or []
        except Exception as e:
            st.error(f"Erro ao carregar dados do Supabase: {e}")
            batalhas_ativas = []

        if not batalhas_ativas:
            st.info("Nenhuma partida em tempo real ativa no momento.")
        else:
            for bat in batalhas_ativas:
                with st.container(border=True):
                    # Organização do card: Info na esquerda, Ações na direita
                    col_info, col_botoes = st.columns([3, 2])
                    
                    with col_info:
                        st.markdown(f"#### ⚔️ {bat['titulo']}")
                        st.markdown(f"*{bat.get('descricao', 'Sem descrição compartilhada.')}*")
                        
                        # Mostra as equipes escaladas se houver
                        t_a = bat.get("time_a", {}).get("nome", "Equipe A") if bat.get("time_a") else None
                        t_b = bat.get("time_b", {}).get("nome", "Equipe B") if bat.get("time_b") else None
                        if t_a and t_b:
                            st.markdown(f"**Confronto:** `{t_a}` vs `{t_b}`")

                        # Crachá de status dinâmico igual ao da imagem
                        status_limpo = str(bat.get("status")).lower()
                        if status_limpo == "agendada":
                            st.markdown("🟡 **Status:** `AGENDADA / AGUARDANDO INÍCIO`")
                        elif status_limpo == "em_andamento":
                            st.markdown("🟢 **Status:** `EM ANDAMENTO / AO VIVO`")
                        else:
                            st.markdown(f"⚫ **Status:** `{status_limpo.upper()}`")

                    with col_botoes:
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Botão padrão de entrada na sala (visto em todas as contas)
                        if st.button("Entrar na Sala", key=f"join_{bat['id']}", type="primary", use_container_width=True):
                            st.session_state.batalha_ativa_id = bat['id']
                            st.session_state.pagina = "batalha_rodada"
                            st.rerun()

                        # 🔥 CONTROLES EXCLUSIVOS DO PROFESSOR EM TEMPO REAL DIRECT CARD
                        if tipo_usuario in ("professor", "admin"):
                            if st.button("🛑 Encerrar e Arquivar", key=f"card_stop_{bat['id']}", type="secondary", use_container_width=True):
                                if encerrar_partida_sincrona(bat['id']):
                                    st.toast("A batalha foi finalizada e arquivada com sucesso!", icon="🛑")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Erro operacional ao encerrar no Supabase.")

                            if st.button("🗑️ Deletar Batalha (Teste)", key=f"card_del_{bat['id']}", type="secondary", use_container_width=True):
                                if deletar_batalha(bat['id']):
                                    st.toast("Batalha de testes removida do sistema!", icon="🗑️")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Erro ao limpar dados do Supabase.")

    # =========================================================================
    # TAB 2: DESAFIOS COM PRAZO (ASSÍNCRONOS)
    # =========================================================================
    with aba_assincrona:
        st.markdown("### 📅 Desafios Práticos")
        st.caption("Analise os enunciados e envie os scripts SQL de resposta dentro do prazo determinado pelo docente.")
        
        # Lógica de listagem assíncrona simples
        try:
            res_assinc = supabase.table("batalhas").select("*").eq("modalidade", "assincrona").eq("finalizada", False).execute()
            batalhas_assinc = res_assinc.data or []
        except Exception:
            batalhas_assinc = []

        if not map(id, batalhas_assinc):
            st.info("Nenhuma lista ou desafio prático estendido publicado no momento.")
        else:
            for b_as in batalhas_assinc:
                with st.container(border=True):
                    st.markdown(f"#### 📝 {b_as['titulo']}")
                    st.markdown(f"Prazo final: `{b_as.get('data_limite', 'Não definido')}`")
                    if st.button("Abrir Caderno de Questões", key=f"open_{b_as['id']}", use_container_width=True):
                        st.session_state.batalha_ativa_id = b_as['id']
                        st.session_state.pagina = "batalha_assincrona_resolucao"
                        st.rerun()