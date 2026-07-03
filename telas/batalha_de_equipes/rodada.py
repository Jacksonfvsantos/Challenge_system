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
    b = obter_estado_batalha(b_id)
    status_atual = b.get("status") if b else None
    if "ultimo_status" not in st.session_state:
        st.session_state.ultimo_status = status_atual
    if st.session_state.ultimo_status != status_atual:
        st.session_state.ultimo_status = status_atual
        st.rerun()

@st.fragment(run_every=5)
def painel_estatistico_reativo(batalha_id, time_a_id, time_b_id, nome_ta, nome_tb):
    pa, pb = calcular_placar_atual(batalha_id, time_a_id, time_b_id)
    st.markdown(f"**Placar:** {nome_ta} {pa} vs {nome_tb} {pb}", unsafe_allow_html=True)

@st.fragment
def renderizador_pergunta_reativo(b_id, tid, ta_id, tb_id, tipo_u):
    b = obter_estado_batalha(b_id)
    p_ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, p_ordem)
    if not dados_p: return

    st.markdown(f"### 📍 {dados_p['enunciado']}")
    tid_limpo = str(tid).strip().lower()
    vez_limpo = str(b.get("time_da_vez_id", "")).strip().lower()
    status = b.get("status_sincrono", "aguardando_resposta")
    
    eh_vez = (tid_limpo == vez_limpo and tipo_u not in ("professor", "admin"))
    
    for alt in dados_p["alternativas"]:
        if st.button(alt["texto"], key=f"alt_{alt['id']}", use_container_width=True, disabled=not eh_vez):
            adv = tb_id if tid_limpo == ta_id.strip().lower() else ta_id
            tentativa = 2 if status == "rebate_ativo" else 1
            processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa)
            st.rerun()

@st.fragment(run_every=1)
def cronometro_reativo(b_id, b):
    inicio = b.get("inicio_turno")
    if not inicio: return
    try:
        inicio_dt = datetime.datetime.fromisoformat(inicio.replace('Z', '+00:00'))
        tempo_passado = (datetime.datetime.now(datetime.timezone.utc) - inicio_dt).total_seconds()
        tempo_restante = 45 - int(tempo_passado)
        if tempo_restante <= 0:
            st.rerun()
        else:
            st.metric("Tempo para responder", f"{tempo_restante}s")
    except: pass

def tela_batalha_rodada():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id: return
    
    monitor_status_reativo(b_id)
    b = obter_estado_batalha(b_id)
    
    if not b or b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()
        
    if b.get("status") == "em_andamento":
        cronometro_reativo(b_id, b)
        renderizador_pergunta_reativo(b_id, *obter_ids_usuario(b))
    else:
        st.info("⏱️ A batalha ainda não começou ou está pausada.")

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

def obter_ids_usuario(b):
    u = st.session_state.get("usuario_logado", {})
    tid = obter_time_do_usuario(u.get("id"))[0]
    return tid, str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip(), str(u.get("tipo_usuario", "aluno")).lower()