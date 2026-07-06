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
        
        # Como a nossa última melhoria já salva os nomes reais, 
        # basta extraí-los diretamente do histórico!
        nome_a = info.get('time_a_nome', 'Time A')
        nome_b = info.get('time_b_nome', 'Time B')
        
        p_a, p_b = info.get('pontos_time_a', 0), info.get('pontos_time_b', 0)
        
        st.balloons()
        
        if p_a > p_b: mensagem = f"🏆 Vencedor: {nome_a}!"
        elif p_b > p_a: mensagem = f"🏆 Vencedor: {nome_b}!"
        else: mensagem = "🤝 Empate!"
            
        cabecalho("🏁 Partida Encerrada!", mensagem)
        
        with st.container(border=True):
            st.markdown(f"### Placar Final: {nome_a} {p_a} x {p_b} {nome_b}")
    
    st.write("")
    if st.button("🏠 Voltar para a Arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()