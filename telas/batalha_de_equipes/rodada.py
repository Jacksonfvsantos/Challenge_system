import streamlit as st
import datetime
from services.batalha_service import (
    encerrar_partida_sincrona, processar_resposta_sincrona, 
    obter_estado_batalha, obter_pergunta_atual, obter_time_do_usuario, 
    calcular_placar_atual, obter_nomes_dos_times
)
from utils.estilo import aplicar_estilo

@st.fragment(run_every=2)
def monitor_de_sincronia_reativo(b_id):
    """Monitora o banco. Se a questão mudar, força RERUN em todos."""
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
            
            processar_resposta_sincrona(
                b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa
            )
            st.rerun()

def tela_batalha_rodada():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id: st.error("ID não encontrado."); return
        
    monitor_de_sincronia_reativo(b_id)
    b = obter_estado_batalha(b_id)
    
    if b.get("status") == "em_andamento":
        u = st.session_state.get("usuario_logado", {})
        tid = obter_time_do_usuario(u.get("id"))[0]
        ta_id, tb_id = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
        nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
        
        st.markdown(f"**Placar:** {nome_ta} {calcular_placar_atual(b_id, ta_id, tb_id)[0]} vs {nome_tb} {calcular_placar_atual(b_id, ta_id, tb_id)[1]}")
        renderizador_pergunta(b_id, tid, ta_id, tb_id, str(u.get("tipo_usuario", "aluno")).lower(), b.get("status_sincrono"))
        
    elif b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()

    if st.button("⬅️ Voltar"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()