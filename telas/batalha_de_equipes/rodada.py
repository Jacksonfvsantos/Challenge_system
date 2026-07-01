import streamlit as st
import time
from services.batalha_service import (
    encerrar_partida_sincrona, processar_resposta_sincrona, 
    processar_resposta_assincrona, obter_estado_batalha, iniciar_partida_sincrona,
    obter_pergunta_atual, obter_time_do_usuario, calcular_placar_atual, obter_nomes_dos_times
)
from utils.estilo import aplicar_estilo

@st.fragment(run_every=3)
def painel_estatistico_reativo(batalha_id, time_a_id, time_b_id, nome_ta, nome_tb):
    pa, pb = calcular_placar_atual(batalha_id, time_a_id, time_b_id)
    st.markdown(f"**Placar:** {nome_ta} {pa} vs {nome_tb} {pb}", unsafe_allow_html=True)

def tela_batalha_rodada():
    aplicar_estilo()
    if st.button("⬅️ Voltar para a Arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()
        
    b_id = st.session_state.get("batalha_ativa_id")
    b = obter_estado_batalha(b_id)
    u = st.session_state.get("usuario_logado", {})
    uid, tid = u.get("id"), obter_time_do_usuario(u.get("id"))[0]
    
    if not b: return
    ta_id, tb_id = str(b.get("time_a_id")).strip(), str(b.get("time_b_id")).strip()
    nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
    
    painel_estatistico_reativo(b_id, ta_id, tb_id, nome_ta, nome_tb)
    p_ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, p_ordem)

    if not dados_p:
        st.warning(f"Aguardando o professor carregar ou liberar a pergunta {p_ordem}...")
        return

    st.markdown(f"### 📍 {dados_p['enunciado']}")

    eh_vez = (str(tid).strip() == str(b.get("time_da_vez_id")).strip())

    adversario_id = tb_id if str(tid).strip() == str(ta_id).strip() else ta_id

    for alt in dados_p["alternativas"]:
        if st.button(alt["texto"], key=f"alt_{alt['id']}", use_container_width=True, disabled=not eh_vez):
            if b.get("modalidade") == "sincrona":
                tentativa = 2 if b.get("status_sincrono") == "rebate_ativo" else 1
                
                res = processar_resposta_sincrona(
                    b_id, dados_p["id"], tid, alt["id"], alt["correta"], 
                    adversario_id, tentativa
                )
                st.toast(f"Resultado: {res}")
            else:
                processar_resposta_assincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"])
                st.success("Resposta registrada!")
            time.sleep(0.5); st.rerun()
    if st.button("🚪 Sair"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()