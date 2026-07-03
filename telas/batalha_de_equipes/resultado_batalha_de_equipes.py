import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

def tela_batalha_resultado():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id: return

    res = supabase.table("historico_batalhas").select("*").eq("batalha_id", b_id).execute()

    if not res.data:
        time.sleep(1)
        res = supabase.table("historico_batalhas").select("*").eq("batalha_id", b_id).execute()
    
    if res.data:
        info = res.data[0]
        t_a_id, t_b_id = info['time_a_nome'], info['time_b_nome']
        
        res_times = supabase.table("times").select("id, nome").in_("id", [t_a_id, t_b_id]).execute()
        mapa_nomes = {str(t['id']): t['nome'] for t in res_times.data}
        
        nome_a = mapa_nomes.get(str(t_a_id), "Time A")
        nome_b = mapa_nomes.get(str(t_b_id), "Time B")
        
        p_a, p_b = info['pontos_time_a'], info['pontos_time_b']
        
        st.balloons()
        
        if p_a > p_b: mensagem = f"🏆 Vencedor: {nome_a}!"
        elif p_b > p_a: mensagem = f"🏆 Vencedor: {nome_b}!"
        else: mensagem = "🤝 Empate!"
            
        cabecalho("🏁 Partida Encerrada!", mensagem)
        
        with st.container(border=True):
            st.markdown(f"### Placar Final: {nome_a} {p_a} x {p_b} {nome_b}")
    
    if st.button("🏠 Voltar para a Arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()