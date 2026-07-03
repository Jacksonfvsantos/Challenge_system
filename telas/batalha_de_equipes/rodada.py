import streamlit as st
import datetime
from database.conexao import supabase
from services.batalha_service import (
    encerrar_partida_sincrona, processar_resposta_sincrona, 
    obter_estado_batalha, obter_pergunta_atual, obter_time_do_usuario, 
    calcular_placar_atual, obter_nomes_dos_times, processar_passagem_de_vez, 
    obter_total_questoes, iniciar_partida_sincrona
)
from utils.estilo import aplicar_estilo

@st.fragment(run_every=2)
def monitor_de_sincronia_reativo(b_id):
    try:
        b = obter_estado_batalha(b_id)
        if not b: return
        ordem_atual = b.get("pergunta_atual_ordem")
        if "ordem_local" not in st.session_state: st.session_state.ordem_local = ordem_atual
        if st.session_state.ordem_local != ordem_atual:
            st.session_state.ordem_local = ordem_atual
            st.rerun() 
    except Exception: pass

@st.fragment
def renderizador_pergunta(b_id, tid, ta_id, tb_id, tipo_u, status):
    b = obter_estado_batalha(b_id)
    ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, ordem)
    if not dados_p: st.info("Aguardando..."); return

    st.markdown(f"### 📍 {dados_p.get('enunciado')}")
    
    tid_limpo = str(tid).strip().lower()
    vez_limpo = str(b.get("time_da_vez_id", "")).strip().lower()
    eh_vez = (tid_limpo == vez_limpo and tipo_u not in ("professor", "admin"))
    
    for alt in dados_p.get("alternativas", []):
        if st.button(alt["texto"], key=f"alt_{alt['id']}", disabled=not eh_vez, use_container_width=True):
            adv = tb_id if tid_limpo == ta_id.strip().lower() else ta_id
            tentativa = 2 if status == "rebate_ativo" else 1
            processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa)
            st.rerun()

@st.fragment(run_every=1)
def cronometro_reativo(b_id, b):
    ordem_atual = int(b.get("pergunta_atual_ordem", 1))
    total_questoes = obter_total_questoes(b_id)
    if ordem_atual > total_questoes:
        st.info("🏁 Todas as questões foram respondidas!")
        return
    inicio = b.get("inicio_turno")
    if not inicio: return
    try:
        inicio_dt = datetime.datetime.fromisoformat(inicio.replace('Z', '+00:00'))
        tempo_passado = (datetime.datetime.now(datetime.timezone.utc) - inicio_dt).total_seconds()
        tempo_restante = 45 - int(tempo_passado)
        if tempo_restante <= 0:
            ta, tb = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
            prox_time = tb if str(b.get("time_da_vez_id", "")).strip() == ta else ta
            processar_passagem_de_vez(b_id, b.get("time_da_vez_id"), prox_time)
            st.rerun()
        else: st.metric("Tempo para responder", f"{tempo_restante}s")
    except Exception: pass

def tela_batalha_rodada():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id: st.error("ID não encontrado."); return
        
    monitor_de_sincronia_reativo(b_id)
    b = obter_estado_batalha(b_id)
    if not b: return

    # --- GOVERNANÇA DOCENTE ---
    if st.session_state.get("usuario_logado", {}).get("tipo_usuario") in ("professor", "admin"):
        with st.expander("⚙️ Governança Docente", expanded=True):
            
            if b.get("status") == "agendada":
                from services.batalha_service import listar_times
                todos_os_times = listar_times()
                
                if todos_os_times:
                    time_selecionado = st.selectbox(
                        "Qual time iniciará a batalha?",
                        options=[t['id'] for t in todos_os_times],
                        format_func=lambda x: next(t['nome'] for t in todos_os_times if t['id'] == x)
                    )
                    
                    if st.button("🚀 Iniciar Partida", type="primary"):
                        if iniciar_partida_sincrona(b_id, time_selecionado):
                            st.success("Partida iniciada!")
                            st.rerun()
                        else:
                            st.error("Erro ao iniciar.")
                else:
                    st.warning("Nenhum time cadastrado no sistema.")

    # --- FLUXO DA PARTIDA ---
    if b.get("status") == "em_andamento":
        u = st.session_state.get("usuario_logado", {})
        tid = obter_time_do_usuario(u.get("id"))[0]
        
        ta_id = str(b.get("time_a_id", "")).strip()
        tb_id = str(b.get("time_b_id", "")).strip()
        
        nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
        
        pa, pb = calcular_placar_atual(b_id, ta_id, tb_id)
        
        st.markdown(f"**Placar:** {nome_ta} ({pa}) vs {nome_tb} ({pb})")
        
        cronometro_reativo(b_id, b)
        renderizador_pergunta(b_id, tid, ta_id, tb_id, str(u.get("tipo_usuario", "aluno")).lower(), b.get("status_sincrono"))
        
    elif b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()
    else:
        st.info("Aguardando início da partida pelo professor.")

    if st.button("⬅️ Voltar"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()