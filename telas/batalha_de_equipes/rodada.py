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
def painel_estatistico_reativo(batalha_id, time_a_id, time_b_id, nome_ta, nome_tb):
    pa, pb = calcular_placar_atual(batalha_id, time_a_id, time_b_id)
    st.markdown(f"**Placar:** {nome_ta} {pa} vs {nome_tb} {pb}", unsafe_allow_html=True)

@st.fragment(run_every=2)
def renderizador_pergunta_reativo(b_id, tid, ta_id, tb_id, tipo_u):
    b = obter_estado_batalha(b_id)
    p_ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, p_ordem)
    
    if not dados_p: return

    st.markdown(f"### 📍 {dados_p['enunciado']}")
    tid_limpo, vez_limpo = str(tid).strip().lower(), str(b.get("time_da_vez_id", "")).strip().lower()
    eh_vez = (tid_limpo == vez_limpo and tipo_u not in ("professor", "admin"))
    
    for alt in dados_p["alternativas"]:
        if st.button(alt["texto"], key=f"alt_{alt['id']}", use_container_width=True, disabled=not eh_vez):
            adv = tb_id if tid_limpo == ta_id.strip().lower() else ta_id
            processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, 1)
            st.rerun()

@st.fragment(run_every=1)
def cronometro_reativo(b_id, b):
    inicio = b.get("inicio_turno")
    if not inicio: return
    
    inicio_dt = datetime.datetime.fromisoformat(inicio.replace('Z', '+00:00'))
    tempo_passado = (datetime.datetime.now(datetime.timezone.utc) - inicio_dt).total_seconds()
    tempo_restante = 45 - int(tempo_passado)
    
    if tempo_restante <= 0:
        ordem_atual = int(b.get("pergunta_atual_ordem", 1))
        novo_time = b.get("time_b_id") if b.get("time_da_vez_id") == b.get("time_a_id") else b.get("time_a_id")
        
        p = obter_pergunta_atual(b_id, ordem_atual)
        if p:
            supabase.table("batalha_respostas").insert({
                "batalha_id": b_id, "questao_id": p["id"], 
                "time_id": b.get("time_da_vez_id"), "resposta_correta": False
            }).execute()
        
        supabase.table("batalhas").update({
            "pergunta_atual_ordem": ordem_atual + 1, "time_da_vez_id": novo_time,
            "inicio_turno": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }).eq("id", b_id).execute()
        st.rerun()
    else:
        st.metric("Tempo para responder", f"{tempo_restante}s")

def tela_batalha_rodada():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    b = obter_estado_batalha(b_id)
    
    if not b or b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()
        
    if "ultima_ordem" not in st.session_state: st.session_state.ultima_ordem = b.get("pergunta_atual_ordem")
    if b.get("pergunta_atual_ordem") != st.session_state.ultima_ordem:
        st.session_state.ultima_ordem = b.get("pergunta_atual_ordem")
        st.rerun()

    p_ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, p_ordem)

    if b.get("status") == "em_andamento" and dados_p:
        cronometro_reativo(b_id, b)
    elif b.get("status") == "em_andamento":
        st.info("🏁 Todas as questões foram respondidas. Aguardando encerramento.")

    u = st.session_state.get("usuario_logado", {})
    tipo_u = str(u.get("tipo_usuario", "aluno")).lower()
    tid = obter_time_do_usuario(u.get("id"))[0]
    ta_id, tb_id = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
    nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)

    if st.button("⬅️ Voltar para a Arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    painel_estatistico_reativo(b_id, ta_id, tb_id, nome_ta, nome_tb)
    renderizador_pergunta_reativo(b_id, tid, ta_id, tb_id, tipo_u)

    if tipo_u in ("professor", "admin"):
        with st.expander("⚙️ Painel de Governança Docente"):
            if b.get("status") == "agendada" and st.button("🔥 Iniciar Partida"):
                from services.batalha_service import iniciar_partida_sincrona
                iniciar_partida_sincrona(b_id, ta_id)
                st.rerun()
            if st.button("⏹️ Encerrar Partida", type="primary"):
                if encerrar_partida_sincrona(b_id):
                    st.session_state.pagina = "batalha_resultado"
                    st.rerun()