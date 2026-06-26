import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho

def tela_resultado_mini_prova():
    aplicar_estilo()
    
    resultado = st.session_state.get("resultado_prova_calculado")
    
    if not resultado:
        st.warning("Nenhum resultado de avaliação foi localizado.")
        if st.button("Voltar ao Painel"):
            st.session_state.pagina = "mini_provas"
            st.rerun()
        return

    cabecalho("📊 Desempenho e Gabarito Processado", "Confira abaixo os seus indicadores nesta avaliação")

    # Exibição de Métricas Reais vindas da correção do banco de dados
    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Nota Final", f"{resultado.get('nota', 0.0)} / 10.0")
    col2.metric("⭐ XP Adquirido", f"+{resultado.get('pontos', 0.0)} pts")
    col3.metric("📈 Taxa de Acertos", resultado.get("acertos", "0/0"))

    st.divider()
    st.subheader("📋 Resumo de Envio")

    if resultado.get("sucesso"):
        st.success("✅ Avaliação registrada e auditada com sucesso na sua carteira de pontuações!")
    else:
        st.error(resultado.get("mensagem", "Erro ao sincronizar notas."))

    # Limpeza preventiva das variáveis de teste para liberar novas provas
    st.divider()
    if st.button("✨ Concluir e Retornar ao Painel Principal", use_container_width=True):
        st.session_state.pop("prova_ativa_id", None)
        st.session_state.pop("caderno_questoes_ativo", None)
        st.session_state.pop("respostas_aluno_atual", None)
        st.session_state.pop("questao_index_atual", None)
        st.session_state.pop("resultado_prova_calculado", None)
        
        st.session_state.pagina = "mini_provas"
        st.rerun()