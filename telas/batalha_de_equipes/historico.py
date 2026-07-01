import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import obter_batalhas_finalizadas

def tela_historico_batalhas():
    aplicar_estilo()
    
    if st.button("⬅️ Voltar ao Painel"):
        st.session_state.pagina = "dashboard_professor"
        st.rerun()
        
    cabecalho("📜 Histórico de Batalhas", "Consulte o desempenho das turmas em eventos passados")
    
    historico = obter_batalhas_finalizadas()
    
    if not historico:
        st.info("Nenhum histórico de batalhas encontrado.")
        return
        
    for h in historico:
        with st.container(border=True):
            st.markdown(f"### {h['titulo']}")
            st.caption(f"Encerrado em: {h['encerrado_em']}")
            st.markdown(f"**Resultado:** {h['resultado_extenso']}")
            st.write(f"📊 Pontuação Final: {h['time_a_nome']} ({h['pontos_time_a']}) vs {h['time_b_nome']} ({h['pontos_time_b']})")