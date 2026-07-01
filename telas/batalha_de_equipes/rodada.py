import streamlit as st
import time

from database.conexao import supabase 
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
    tipo_u = str(u.get("tipo_usuario", "aluno")).lower()
    uid = u.get("id")
    times_usuario = obter_time_do_usuario(uid)
    tid = times_usuario[0] if times_usuario else None
    
    if not b: return
    ta_id, tb_id = str(b.get("time_a_id")).strip(), str(b.get("time_b_id")).strip()
    nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
    
    painel_estatistico_reativo(b_id, ta_id, tb_id, nome_ta, nome_tb)
    
    p_ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, p_ordem)

    if not dados_p:
        st.warning(f"Nenhuma pergunta encontrada para a ordem {p_ordem}.")
        
        if tipo_u in ("professor", "admin"):
            st.write("---")
            st.write("🔍 **Diagnóstico do Docente:**")

            try:
                res_debug = supabase.table("batalha_perguntas")\
                    .select("*", count='exact')\
                    .eq("batalha_id", b_id)\
                    .execute()
                
                total_questoes = res_debug.count if res_debug.count is not None else 0
                st.info(f"Total de questões vinculadas a esta batalha: {total_questoes}")
                
                if total_questoes == 0:
                    st.error("⚠️ Atenção: Não há questões cadastradas para esta batalha.")
            except Exception as e:
                st.error(f"Erro ao contar questões: {e}")
            
            if st.button("🔄 Forçar reset da Batalha para Pergunta 1"):
                supabase.table("batalhas").update({"pergunta_atual_ordem": 1, "status": "em_andamento"}).eq("id", b_id).execute()
                st.rerun()
        return

    st.markdown(f"### 📍 {dados_p['enunciado']}")

    eh_vez = (str(tid).strip() == str(b.get("time_da_vez_id")).strip())
    adversario_id = tb_id if str(tid).strip() == str(ta_id).strip() else ta_id

    for alt in dados_p["alternativas"]:
        eh_professor = tipo_u in ("professor", "admin")
        if st.button(alt["texto"], key=f"alt_{alt['id']}", use_container_width=True, disabled=not eh_vez and not eh_professor):
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