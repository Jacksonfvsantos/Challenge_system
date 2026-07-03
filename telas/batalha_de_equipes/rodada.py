import streamlit as st
from services.batalha_service import (
    obter_estado_batalha, obter_pergunta_atual, processar_resposta_sincrona, 
)
from utils.estilo import aplicar_estilo

def tela_batalha_rodada():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    
    if not b_id:
        st.error("Nenhuma batalha ativa selecionada.")
        if st.button("Voltar"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()
        return

    b = obter_estado_batalha(b_id)
    if not b: return

    if b.get("status") == "agendada":
        st.info("⏱️ Aguardando o professor iniciar a partida...")
        if st.button("Atualizar Estado"): st.rerun()
        
    elif b.get("status") == "em_andamento":
        renderizar_arena_ativa(b)
        
    elif b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()

def renderizar_arena_ativa(b):
    ordem = b.get("pergunta_atual_ordem", 1)
    questao = obter_pergunta_atual(b["id"], ordem)
    
    st.markdown(f"### Questão {ordem}")
    st.write(questao["enunciado"])
    
    for alt in questao["alternativas"]:
        if st.button(alt["texto"]):
            processar_resposta_sincrona(b["id"], ...)
            st.rerun()

@st.fragment(run_every=2)
def monitor_de_sincronia_reativo(b_id):
    """
    Monitora a tabela de batalhas no banco. Se o número da questão (pergunta_atual_ordem)
    ou o status da batalha mudarem, força o refresh da tela de todos os alunos.
    """
    try:
        b = obter_estado_batalha(b_id)
        if not b: return
        
        ordem_banco = b.get("pergunta_atual_ordem")
        status_banco = b.get("status")
        
        if "ordem_local" not in st.session_state:
            st.session_state.ordem_local = ordem_banco
        if "status_local" not in st.session_state:
            st.session_state.status_local = status_banco
            
        if st.session_state.ordem_local != ordem_banco or st.session_state.status_local != status_banco:
            st.session_state.ordem_local = ordem_banco
            st.session_state.status_local = status_banco
            st.rerun()
            
    except Exception: 
        pass