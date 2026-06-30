import streamlit as st
import time
from utils.estilo import aplicar_estilo, cabecalho
from utils.compartilhamento import exibir_painel_compartilhamento
from services.quiz_ao_vivo_service import listar_quizzes, deletar_quiz, atualizar_status_quiz

def tela_quiz_ao_vivo():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho("🎮 Quiz ao Vivo", "Participe de rodadas síncronas em tempo real")

    quizzes = listar_quizzes()

    for q in quizzes:
        q_id = q["id"]
        status = q.get("status", "criado")
        
        with st.container(border=True):
            st.subheader(q["titulo"])
            st.caption(f"Disciplina: {q.get('disciplina')} | Status: {status}")
            
            if tipo in ("professor", "admin"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Configurar Perguntas", key=f"conf_{q_id}"):
                        st.session_state.pagina = "cadastro_perguntas_quiz"
                        st.session_state.quiz_id_selecionado = q_id
                        st.rerun()
                with col2:
                    if st.button("🗑️ Deletar Sala", key=f"del_{q_id}", type="primary"):
                        if deletar_quiz(q_id):
                            st.rerun()
            else:
                if status in ("em_andamento", "ativo"):
                    if st.button("🎯 Ingressar na Sala", key=f"join_{q_id}", type="primary"):
                        st.session_state.quiz_ativo_id = q_id
                        st.session_state.pagina = "quiz_rodada"
                        st.rerun()