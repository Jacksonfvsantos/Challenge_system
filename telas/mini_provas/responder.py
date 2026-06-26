import streamlit as st
import time
from services.mini_prova_service import buscar_mini_prova, computar_resultado_avaliacao

def tela_responder_mini_prova():
    # Validações de segurança de escopo
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

    TEMPO_TOTAL_SEGUNDOS = int(prova["duracao_minutos"] * 60)

    # Inicializa o marco temporal do início do teste
    if st.session_state.get("timestamp_inicio_prova") is None:
        st.session_state.timestamp_inicio_prova = time.time()
    if "questao_index_atual" not in st.session_state:
        st.session_state.questao_index_atual = 0
    if "respostas_aluno_atual" not in st.session_state:
        st.session_state.respostas_aluno_atual = {}

    # Calcula tempo restante real
    tempo_passado = time.time() - st.session_state.timestamp_inicio_prova
    tempo_restante = max(0, TEMPO_TOTAL_SEGUNDOS - int(tempo_passado))

    # TELA DE TEMPO ESGOTADO (Submissão forçada com o que foi respondido)
    if tempo_restante <= 0:
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; text-align: center;">
            <div style="background: #fff5f5; border: 1px solid #e53e3e; border-radius: 12px; padding: 35px; max-width: 500px;">
                <div style="font-size: 48px; margin-bottom: 16px;">⏱️</div>
                <div style="font-size: 20px; font-weight: bold; color: #e53e3e; margin-bottom: 8px;">Tempo Limite Esgotado!</div>
                <div style="font-size: 14px; color: #666;">Sua avaliação foi encerrada pelo sistema. Suas respostas preenchidas até o momento estão sendo computadas.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Verificar Meu Resultado Forçado", use_container_width=True, type="primary"):
            res = computar_resultado_avaliacao(usuario["id"], prova_id, st.session_state.respostas_aluno_atual, caderno)
            st.session_state.resultado_prova_calculado = res
            st.session_state.pagina = "resultado_mini_prova"
            st.rerun()
        return

    # COMPONENTE VISUAL DO CRONÔMETRO DE TOPO FIXO
    minutos = tempo_restante // 60
    segundos = tempo_restante % 60
    cor_tempo = "#e53e3e" if tempo_restante <= 30 else "#1b3a5c"

    st.markdown(f"""
    <div style="position: fixed; top: 60px; right: 24px; z-index: 999; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 14px; color: #64748b; font-weight:600;">⏱️ Tempo Restante:</span>
        <span style="font-size: 16px; font-weight: 700; color: {cor_tempo}; font-variant-numeric: tabular-nums;">
            {minutos:02d}:{segundos:02d}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # CONTROLADOR DE PROGRESSO DA PROVA
    total_questoes = len(caderno)
    questao_idx = st.session_state.questao_index_atual
    progresso_percentual = (questao_idx + 1) / total_questoes

    st.caption(f"**Questão {questao_idx + 1} de {total_questoes}**")
    st.progress(progresso_percentual)

    # RENDERIZAÇÃO DA QUESTÃO DO CADERNO ATIVO
    questao = caderno[questao_idx]
    
    # Mapeamento dinâmico vindo do caderno relacional estruturado pelo novo service
    opcoes_alternativas = questao.get("alternativas", [])
    if questao.get("alternativa_a"): opcoes_alternativas.append(questao["alternativa_a"])
    if questao.get("alternativa_b"): opcoes_alternativas.append(questao["alternativa_b"])
    if questao.get("alternativa_c"): opcoes_alternativas.append(questao["alternativa_c"])
    if questao.get("alternativa_d"): opcoes_alternativas.append(questao["alternativa_d"])
    if questao.get("alternativa_e"): opcoes_alternativas.append(questao["alternativa_e"])

    # Recupera se o aluno já tinha marcado alguma opção nesta questão (Navegação segura)
    resposta_salva = st.session_state.respostas_aluno_atual.get(questao_idx)
    index_opcao_salva = opcoes_alternativas.index(resposta_salva) if resposta_salva in opcoes_alternativas else None

    with st.container(border=True):
        st.markdown(f"#### {questao['enunciado']}")
        st.divider()
        
        escolha = st.radio(
            "Selecione a alternativa correta:",
            opcoes_alternativas,
            index=index_opcao_salva,
            key=f"render_q_{questao_idx}"
        )

    # BARRA DE DIRECIONAMENTO E FLUXO (BOTÕES)
    st.write("")
    col_ant, col_prox = st.columns(2)

    with col_ant:
        if questao_idx > 0:
            if st.button("⬅️ Questão Anterior", use_container_width=True):
                if escolha:
                    st.session_state.respostas_aluno_atual[questao_idx] = escolha
                st.session_state.questao_index_atual -= 1
                st.rerun()

    with col_prox:
        if questao_idx < total_questoes - 1:
            if st.button("Próxima Questão ➡️", use_container_width=True):
                if escolha is None:
                    st.warning("Por favor, selecione uma alternativa antes de avançar.")
                else:
                    st.session_state.respostas_aluno_atual[questao_idx] = escolha
                    st.session_state.questao_index_atual += 1
                    st.rerun()
        else:
            # Última Questão: Finalizar e Corrigir Automaticamente pelo Service
            if st.button("🏁 Finalizar e Entregar Prova", use_container_width=True, type="primary"):
                if escolha is None:
                    st.warning("Selecione uma alternativa para poder concluir a avaliação.")
                else:
                    st.session_state.respostas_aluno_atual[questao_idx] = escolha
                    
                    with st.spinner("Corrigindo gabarito e computando XP..."):
                        resultado_final = computar_resultado_avaliacao(
                            usuario["id"], 
                            prova_id, 
                            st.session_state.respostas_aluno_atual, 
                            caderno
                        )
                        st.session_state.resultado_prova_calculado = resultado_final
                        st.session_state.pagina = "resultado_mini_prova"
                        st.rerun()

    # Thread de atualização de 1 segundo para manter o cronômetro síncrono
    time.sleep(1)
    st.rerun()