import streamlit as st
import datetime
from database.conexao import supabase 
from services.batalha_service import (
    encerrar_partida_sincrona, processar_resposta_sincrona, 
    obter_estado_batalha, obter_pergunta_atual, obter_time_do_usuario, 
    calcular_placar_atual, obter_nomes_dos_times
)
from utils.estilo import aplicar_estilo

@st.fragment(run_every=2)
def monitor_status_reativo(b_id):
    try:
        b = obter_estado_batalha(b_id)
        status_atual = b.get("status") if b else "finalizada"
        
        if st.session_state.get("ultimo_status") != status_atual:
            st.session_state.ultimo_status = status_atual
            st.rerun() 
    except Exception: pass

@st.fragment(run_every=5)
def painel_estatistico_reativo(batalha_id, time_a_id, time_b_id, nome_ta, nome_tb):
    try:
        pa, pb = calcular_placar_atual(batalha_id, time_a_id, time_b_id)
        st.markdown(f"**Placar:** {nome_ta} {pa} vs {nome_tb} {pb}", unsafe_allow_html=True)
    except Exception: st.error("Erro ao carregar placar.")

@st.fragment
def renderizador_pergunta_reativo(b_id, tid, ta_id, tb_id, tipo_u):
    try:
        b = obter_estado_batalha(b_id)
        if not b: return
        p_ordem = int(b.get("pergunta_atual_ordem", 1))
        dados_p = obter_pergunta_atual(b_id, p_ordem)
        if not dados_p: 
            st.info("Aguardando próxima questão...")
            return

        st.markdown(f"### 📍 {dados_p.get('enunciado', 'Sem enunciado')}")
        
        tid_limpo = str(tid).strip().lower()
        vez_limpo = str(b.get("time_da_vez_id", "")).strip().lower()
        status = b.get("status_sincrono", "aguardando_resposta")
        
        eh_vez = (tid_limpo == vez_limpo and tipo_u not in ("professor", "admin"))
        
        for alt in dados_p.get("alternativas", []):
            if st.button(alt.get("texto", ""), key=f"alt_{alt.get('id')}", use_container_width=True, disabled=not eh_vez):
                adv = tb_id if tid_limpo == ta_id.strip().lower() else ta_id
                tentativa = 2 if status == "rebate_ativo" else 1
                processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa)
                st.rerun()
    except Exception as e: st.error(f"Erro no renderizador: {e}")

@st.fragment(run_every=1)
def cronometro_reativo(b_id, b):
    inicio = b.get("inicio_turno")
    if not inicio: return
    try:
        inicio_dt = datetime.datetime.fromisoformat(inicio.replace('Z', '+00:00'))
        tempo_passado = (datetime.datetime.now(datetime.timezone.utc) - inicio_dt).total_seconds()
        tempo_restante = 45 - int(tempo_passado)
        if tempo_restante <= 0: st.rerun()
        else: st.metric("Tempo para responder", f"{tempo_restante}s")
    except Exception: pass

def tela_batalha_rodada():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id:
        st.warning("ID da batalha não encontrado.")
        return
        
    monitor_status_reativo(b_id)
    b = obter_estado_batalha(b_id)
    
    if not b or b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()
        
    if b.get("status") == "em_andamento":
        cronometro_reativo(b_id, b)
        u = st.session_state.get("usuario_logado", {})
        tid_lista = obter_time_do_usuario(u.get("id"))
        tid = tid_lista[0] if tid_lista else ""
        ta_id, tb_id = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
        nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
        
        painel_estatistico_reativo(b_id, ta_id, tb_id, nome_ta, nome_tb)
        renderizador_pergunta_reativo(b_id, tid, ta_id, tb_id, str(u.get("tipo_usuario", "aluno")).lower())
    else:
        st.info("⏱️ A batalha ainda não começou.")

    if st.button("⬅️ Voltar para a Arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    if st.session_state.get("usuario_logado", {}).get("tipo_usuario") in ("professor", "admin"):
        with st.expander("⚙️ Governança Docente"):
            if b.get("status") == "agendada" and st.button("🔥 Iniciar Partida"):
                from services.batalha_service import iniciar_partida_sincrona
                iniciar_partida_sincrona(b_id, b.get("time_a_id"))
                st.rerun()
            if st.button("⏹️ Encerrar Partida", type="primary"):
                encerrar_partida_sincrona(b_id)
                st.session_state.pagina = "batalha_resultado"
                st.rerun()