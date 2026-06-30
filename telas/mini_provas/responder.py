import streamlit as st
import time
from services.mini_prova_service import buscar_mini_prova, computar_resultado_avaliacao
from utils.estilo import aplicar_estilo, cabecalho

def exibir_diretrizes(prova):
    """Renderiza o painel de diretrizes dinâmicas configuradas pelo professor."""
    st.markdown(f"""
    <div style="background:#fffaf0; padding:20px; border-radius:10px; border:1px solid #ecc94b; margin-bottom: 25px;">
        <h4 style="color:#744210; margin-top: 0;">⚠️ Diretrizes Obrigatórias de Avaliação:</h4>
        <ul style="color:#744210;">
            <li><b>Componente Curricular:</b> {prova.get('disciplina', 'Não definido')}</li>
            <li><b>Duração Limite:</b> O cronômetro de <b>{prova.get('duracao_minutos', 0)} minutos</b> começará imediatamente.</li>
            <li><b>Persistência visual:</b> Você não deve fechar ou recarregar a página (F5), caso contrário o progresso atual será perdido.</li>
            <li><b>Pontuação Máxima:</b> Esta atividade vale até <b>{prova.get('pontos_xp', 0)} pontos</b> na trilha de XP.</li>
        </ul>
        <p style="color:#744210; font-size:0.9em;">
            <b>Instruções:</b> {prova.get('instrucoes', 'Leia atentamente antes de iniciar.')}
        </p>
    </div>
    """, unsafe_allow_html=True)

def tela_responder_mini_prova():
    aplicar_estilo()
    prova_id = st.session_state.get("prova_ativa_id")
    caderno = st.session_state.get("caderno_questoes_ativo")
    usuario = st.session_state.get("usuario_logado")

    if not prova_id or not caderno or not usuario:
        st.error("❌ Sessão de avaliação inválida ou expirada.")
        if st.button("Voltar para o Painel"):
            st.session_state.pagina = "mini_provas"
            st.rerun()
        return

    prova = buscar_mini_prova(prova_id)
    if not prova:
        st.error("Prova não localizada.")
        return

    cabecalho(f"Executar: {prova.get('titulo', 'Avaliação')}", "Leia as instruções atentamente antes de iniciar")
    
    if st.session_state.get("timestamp_inicio_prova") is None:
        exibir_diretrizes(prova)
        if st.button("✅ Li e compreendi as diretrizes, Iniciar Prova", type="primary", use_container_width=True):
            st.session_state.timestamp_inicio_prova = time.time()
            st.rerun()
        return

    TEMPO_TOTAL_SEGUNDOS = int(prova["duracao_minutos"] * 60)
    tempo_passado = time.time() - st.session_state.timestamp_inicio_prova
    tempo_restante = max(0, TEMPO_TOTAL_SEGUNDOS - int(tempo_passado))

    if tempo_restante <= 0:
        st.markdown("""<div style="text-align: center; padding: 40px; color: #e53e3e;">⏱️ Tempo esgotado!</div>""", unsafe_allow_html=True)
        if st.button("Verificar Resultado", use_container_width=True, type="primary"):
            res = computar_resultado_avaliacao(usuario["id"], prova_id, st.session_state.respostas_aluno_atual, caderno)
            st.session_state.resultado_prova_calculado = res
            st.session_state.pagina = "resultado_mini_prova"
            st.rerun()
        return

    minutos, segundos = tempo_restante // 60, tempo_restante % 60
    st.markdown(f"""
    <div style="position: fixed; top: 60px; right: 24px; z-index: 999; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        <span style="font-weight:600;">⏱️ Tempo:</span> {minutos:02d}:{segundos:02d}
    </div>
    """, unsafe_allow_html=True)
    if "questao_index_atual" not in st.session_state: st.session_state.questao_index_atual = 0
    if "respostas_aluno_atual" not in st.session_state: st.session_state.respostas_aluno_atual = {}

    questao_idx = st.session_state.questao_index_atual
    total_questoes = len(caderno)
    questao = caderno[questao_idx]
    opcoes = [questao.get(f"alternativa_{l}") for l in ['a', 'b', 'c', 'd', 'e'] if questao.get(f"alternativa_{l}")]
    
    with st.container(border=True):
        st.markdown(f"#### {questao['enunciado']}")
        escolha = st.radio("Selecione:", opcoes, key=f"q_{questao_idx}")

    col_ant, col_prox = st.columns(2)
    with col_ant:
        if questao_idx > 0 and st.button("⬅️ Anterior"):
            st.session_state.respostas_aluno_atual[questao_idx] = escolha
            st.session_state.questao_index_atual -= 1
            st.rerun()
    with col_prox:
        if questao_idx < total_questoes - 1:
            if st.button("Próxima ➡️"):
                st.session_state.respostas_aluno_atual[questao_idx] = escolha
                st.session_state.questao_index_atual += 1
                st.rerun()
        else:
            if st.button("🏁 Finalizar Prova", type="primary"):
                st.session_state.respostas_aluno_atual[questao_idx] = escolha
                resultado_final = computar_resultado_avaliacao(usuario["id"], prova_id, st.session_state.respostas_aluno_atual, caderno)
                st.session_state.resultado_prova_calculado = resultado_final
                st.session_state.pagina = "resultado_mini_prova"
                st.rerun()