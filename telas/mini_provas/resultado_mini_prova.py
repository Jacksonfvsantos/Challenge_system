import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho

def tela_resultado_mini_prova():
    aplicar_estilo()
    
    resultado = st.session_state.get("resultado_prova_calculado")
    caderno = st.session_state.get("caderno_questoes_ativo")
    respostas_aluno = st.session_state.get("respostas_aluno_atual")
    
    if not resultado:
        st.warning("⚠️ Nenhum resultado de avaliação foi localizado para revisão imediata.")
        if st.button("Voltar ao Painel"):
            st.session_state.pagina = "mini_provas"
            st.rerun()
        return

    cabecalho("📊 Desempenho e Gabarito Processado", "Confira abaixo os seus indicadores nesta avaliação")

    # 📈 Painel Superior de Métricas Reais (Conectado ao DDL de historico_provas)
    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Nota Final", f"{resultado.get('nota', 0.0)} / 10.0")
    col2.metric("⭐ XP Adquirido", f"+{resultado.get('pontos', 0.0)} pts")
    col3.metric("📈 Taxa de Acertos", resultado.get("acertos", "0/0"))

    st.divider()
    
    # 📋 Exibição do Gabarito Detalhado (Se a sessão contiver o caderno ativo do teste atual)
    if caderno and respostas_aluno:
        st.subheader("🔍 Revisão Questão por Questão")
        st.caption("Veja abaixo os enunciados, a alternativa que você selecionou e o gabarito oficial.")
        
        for idx, questao in enumerate(caderno):
            resp_aluno = respostas_aluno.get(idx)
            gabarito_oficial = questao.get("gabarito_texto")
            
            # Define o status de acerto para estilização do bloco
            foi_correto = (str(resp_aluno).strip() == str(gabarito_oficial).strip())
            cor_container = "#e6f4ea" if foi_correto else "#fce8e6"
            cor_borda = "#137333" if foi_correto else "#c5221f"
            
            with st.container(border=True):
                st.markdown(f"""
                <div style="background: {cor_container}; border-left: 5px solid {cor_borda}; padding: 10px 14px; border-radius: 4px;">
                    <strong style="color: #1b3a5c;">Questão {idx + 1}:</strong> {questao.get('enunciado')}
                </div>
                """, unsafe_allow_html=True)
                
                # Renderiza a lista de opções marcando visualmente os status
                st.markdown("<br>", unsafe_allow_html=True)
                for alt_texto in questao.get("alternativas", []):
                    if alt_texto == gabarito_oficial:
                        st.success(f"🟢 **[Gabarito Oficial]:** {alt_texto}")
                    elif alt_texto == resp_aluno and not foi_correto:
                        st.error(f"🔴 **[Sua Resposta Incorreta]:** {alt_texto}")
                    else:
                        st.markdown(f"⚪ {alt_texto}")
                st.write("")
    else:
        # Fallback caso ele esteja acessocando uma prova antiga vindo da tela de histórico
        st.info("ℹ️ Para revisar o caderno de perguntas completo, realize uma nova tentativa da mini-prova. Seu log de notas permanece auditado com sucesso na base!")

    if resultado.get("sucesso") and not caderno:
        st.success("✅ Avaliação registrada e sincronizada com sucesso na sua carteira de pontuações!")

    # 🧹 Limpeza cirúrgica das variáveis temporárias de execução para liberar novos testes
    st.divider()
    if st.button("✨ Concluir e Retornar ao Painel Principal", use_container_width=True, type="primary"):
        st.session_state.pop("prova_ativa_id", None)
        st.session_state.pop("caderno_questoes_ativo", None)
        st.session_state.pop("respostas_aluno_atual", None)
        st.session_state.pop("questao_index_atual", None)
        st.session_state.pop("resultado_prova_calculado", None)
        
        st.session_state.pagina = "mini_provas"
        st.rerun()