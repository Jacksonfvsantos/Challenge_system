import time

import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho
from services.quiz_ao_vivo_service import listar_quizzes, criar_quiz, deletar_quiz

def tela_quiz_ao_vivo():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()
    usuario_id = usuario.get("id")
    
    cabecalho("🎮 Quiz em Tempo Real", "Teste o seu conhecimento")

    if tipo in ("professor", "admin"):
        with st.expander("➕ Criar Nova Sala de Quiz"):
            with st.form("form_novo_quiz", clear_on_submit=True):
                col1, col2 = st.columns(2)
                titulo = col1.text_input("Título da Sala")
                disciplina = col2.text_input("Disciplina")
                tema = st.text_input("Tema do Quiz")
                
                if st.form_submit_button("Criar Sala"):
                    if titulo:
                        res = criar_quiz(titulo, usuario_id, disciplina, tema)
                        if res["sucesso"]:
                            st.success(res["mensagem"])
                            st.rerun()
                        else:
                            st.error(res["mensagem"])
                    else:
                        st.warning("O título é obrigatório.")

    quizzes = listar_quizzes()
    
    if not quizzes:
        st.info("Nenhuma sala de quiz disponível no momento.")
    else:
        for q in quizzes:
            q_id = q["id"]
            status = q.get("status", "criado")
            
            with st.container(border=True):
                col_info, col_acao = st.columns([3, 1])
                with col_info:
                    st.markdown(f"#### {q['titulo']}")
                    st.caption(f"Tema: {q.get('tema')} | Status: {status}")
                
                with col_acao:
                    if tipo in ("professor", "admin"):
                        # Botão de Configurar
                        if st.button("⚙️ Configurar", key=f"conf_{q_id}", use_container_width=True):
                            st.session_state.pagina = "cadastro_perguntas_quiz"
                            st.session_state.quiz_id_selecionado = q_id
                            st.rerun()
                        
                        # Botão de Deletar com feedback imediato
                        if st.button("🗑️ Deletar", key=f"del_{q_id}", type="primary", use_container_width=True):
                            # Chamada direta para o serviço
                            from services.quiz_ao_vivo_service import deletar_quiz
                            sucesso = deletar_quiz(q_id)
                            
                            if sucesso:
                                st.toast("Quiz removido com sucesso!", icon="✅")
                                time.sleep(0.5) # Pequena pausa para garantir a persistência
                                st.rerun()
                            else:
                                st.error("Não foi possível excluir. Verifique se existem perguntas associadas.")
                    else:
                        if status in ("em_andamento", "ativo", "criado"): 
                            if st.button("🎯 Ingressar", key=f"join_{q_id}", type="primary", use_container_width=True):
                                st.session_state.quiz_ativo_id = q_id
                                st.session_state.pagina = "quiz_rodada"
                                st.rerun()
                        else:
                            st.button("🔒 Encerrado", key=f"lock_{q_id}", disabled=True, use_container_width=True)
                
                # --- INTEGRAÇÃO DO QR CODE (REQUISITO DE RELATÓRIO) ---
                if tipo in ("professor", "admin"):
                    with st.expander("📡 Painel de Compartilhamento (QR Code / Link)"):
                        from utils.compartilhamento import exibir_painel_compartilhamento
                        exibir_painel_compartilhamento("quiz", q_id)