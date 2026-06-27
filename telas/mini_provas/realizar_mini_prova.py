import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho
from services.mini_prova_service import buscar_mini_prova, gerar_caderno_questoes_dinamico

def tela_realizar_mini_prova():
    aplicar_estilo()
    
    prova_id = st.session_state.get("prova_ativa_id")
    if not prova_id:
        st.warning("⚠️ Nenhuma mini prova foi selecionada para execução.")
        if st.button("Voltar para a Lista"):
            st.session_state.pagina = "mini_provas"
            st.rerun()
        return

    prova = buscar_mini_prova(prova_id)
    if not prova:
        st.error("❌ Erro ao carregar os dados da mini prova.")
        return

    cabecalho(f"📝 Executar: {prova.get('titulo')}", "Leia as instruções atentamente antes de iniciar")

    st.markdown(f"""
    <div style="background:#fff3e0; border-left:4px solid #ff9800; border-radius:8px; padding:14px 18px; margin-bottom:16px;">
        <strong style="color:#0d1b2a; font-size:16px;">⚠️ Diretrizes Obrigatórias de Avaliação:</strong>
        <ul style="color:#555; margin:8px 0 0; padding-left:18px; font-size:14px; line-height:1.6;">
            <li><strong>Componente Curricular:</strong> {prova.get('disciplina')} ({prova.get('assunto')})</li>
            <li><strong>Duração Limite:</strong> O cronômetro de <strong>{prova.get('duracao_minutos')} minutos</strong> começará imediatamente.</li>
            <li><strong>Persistência visual:</strong> Você não deve fechar ou recarregar a página (F5), caso contrário o progresso atual será perdido.</li>
            <li><strong>Pontuação Máxima:</strong> Esta atividade vale até <strong>{prova.get('pontos_maximos')} pontos</strong> na trilha de XP.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Iniciar e Começar Cronômetro", use_container_width=True, type="primary"):
        with st.spinner("Sorteando caderno de questões exclusivo..."):
            caderno = gerar_caderno_questoes_dinamico(prova_id)
            
            if not caderno:
                st.error("Erro: O banco de dados não possui questões cadastradas para esta disciplina/assunto.")
            else:
                st.session_state.caderno_questoes_ativo = caderno
                st.session_state.respostas_aluno_atual = {}
                st.session_state.questao_index_atual = 0
                st.session_state.timestamp_inicio_prova = None
                
                st.session_state.pagina = "prova_responder"
                st.rerun()

    st.divider()
    if st.button("⬅️ Voltar"):
        st.session_state.pagina = "mini_provas"
        st.rerun()