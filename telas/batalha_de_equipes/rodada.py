import streamlit as st
from database.conexao import supabase
from services.batalha_service import (
    obter_estado_batalha, processar_resposta_sincrona, 
    obter_pergunta_atual, obter_time_do_usuario, 
    calcular_placar_atual, obter_nomes_dos_times
)
from utils.estilo import aplicar_estilo

def tela_batalha_rodada():
    aplicar_estilo()
    
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id:
        st.error("Nenhuma arena selecionada.")
        if st.button("Voltar"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()
        return

    b = obter_estado_batalha(b_id)
    if not b:
        st.error("Erro ao carregar dados da partida.")
        return

    # --- FLUXO DA PARTIDA ---
    if b.get("status") == "em_andamento":
        u = st.session_state.get("usuario_logado", {})
        # Busca o ID do time de forma segura
        time_info = obter_time_do_usuario(u.get("id"))
        tid = time_info[0] if time_info else None
        
        ta_id, tb_id = str(b.get("time_a_id", "")), str(b.get("time_b_id", ""))
        pa, pb = calcular_placar_atual(b_id, ta_id, tb_id)
        nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
        
        st.subheader(f"Placar: {nome_ta} ({pa}) x {nome_tb} ({pb})")
        
        # Renderização da pergunta atual
        ordem = int(b.get("pergunta_atual_ordem", 1))
        dados_p = obter_pergunta_atual(b_id, ordem)
        
        if dados_p:
            st.markdown(f"### {dados_p.get('enunciado')}")
            
            # Validação simples da vez
            eh_vez = (str(tid) == str(b.get("time_da_vez_id")))
            
            for alt in dados_p.get("alternativas", []):
                if st.button(alt["texto"], key=f"alt_{alt['id']}", disabled=not eh_vez):
                    adv = tb_id if str(tid) == ta_id else ta_id
                    tentativa = 2 if b.get("status_sincrono") == "rebate_ativo" else 1
                    
                    resultado = processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa)
                    st.rerun()
        else:
            st.info("Aguardando próxima questão...")
            
    else:
        st.info("Partida não iniciada ou encerrada.")

    if st.button("Sair da Arena"): 
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()