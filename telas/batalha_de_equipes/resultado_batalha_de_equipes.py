import streamlit as st
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

def tela_batalha_resultado():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    
    if not b_id:
        st.info("Nenhuma batalha ativa para exibir resultados.")
        return

    res = supabase.table("historico_batalhas").select("*").eq("batalha_id", b_id).execute()
    
    if res.data:
        info = res.data[0]
        st.balloons()
        
        p_a, p_b = info['pontos_time_a'], info['pontos_time_b']
        nome_a, nome_b = info['time_a_nome'], info['time_b_nome']

        if p_a > p_b:
            mensagem = f"🏆 Vencedor: {nome_a}!"
        elif p_b > p_a:
            mensagem = f"🏆 Vencedor: {nome_b}!"
        else:
            mensagem = "🤝 Partida terminou em Empate!"
            
        cabecalho("🏁 Partida Encerrada!", mensagem)
        
        with st.container(border=True):
            st.markdown(f"### {info['resultado_extenso']}")
            st.write(f"**Placar Final:** {nome_a} **{p_a}** x **{p_b}** {nome_b}")
    else:
        st.error("Erro ao carregar o resultado da batalha.")
    
    if st.button("🏠 Voltar para a Arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()