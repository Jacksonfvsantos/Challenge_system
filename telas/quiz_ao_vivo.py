import streamlit as st
import pandas as pd
import time
import datetime
from utils.estilo import aplicar_estilo, cabecalho
from services.quiz_ao_vivo_service import criar_quiz, deletar_quiz
from utils.compartilhamento import exibir_painel_compartilhamento
from database.conexao import supabase

def listar_quizzes_do_banco():
    try:
        res = supabase.table("quizzes").select("*").order("data_criacao", desc=True).execute()
        return res.data or []
    except Exception as e:
        try:
            res = supabase.table("quizzes").select("*").execute()
            return res.data or []
        except Exception:
            return []

def alterar_status_quiz(quiz_id, novo_status):
    try:
        supabase.table("quizzes").update({"status": novo_status}).eq("id", quiz_id).execute()
        return True
    except Exception:
        return False


def tela_quiz_ao_vivo():
    aplicar_estilo()

    usuario = st.session_state.get("usuario_logado", {})
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()
    user_id = usuario.get("id")

    cabecalho(
        "🎮 Quiz Acadêmico ao Vivo",
        "Participe de sessões síncronas de perguntas e respostas em sala de aula"
    )

    # ⏱️ AUTO-REFRESH SÍNCRONO: Injeta um script leve em HTML que atualiza a tela do aluno a cada 3 segundos
    if tipo == "aluno":
        st.components.v1.html(
            """
            <script>
                if (!window.refreshIntervalSet) {
                    window.refreshIntervalSet = true;
                    setInterval(function() {
                        window.parent.postMessage({type: 'streamlit:setComponentValue', value: true}, '*');
                    }, 3000);
                }
            </script>
            """,
            height=0
        )

    if tipo in ("professor", "admin"):
        aba_gestao, aba_lista = st.tabs(["✨ Criar Novo Quiz", "📊 Painel de Controle Síncrono"])
    else:
        aba_lista, = st.tabs(["🎮 Quizzes Disponíveis"])

    if tipo in ("professor", "admin"):
        with aba_gestao:
            st.subheader("Configurar Nova Sessão de Quiz")
            st.caption("Crie um quiz síncrono mapeado por componentes curriculares para revisão de conteúdo.")
            
            with st.form("form_novo_quiz_sincrono", clear_on_submit=False):
                titulo = st.text_input("Título do Quiz", placeholder="Ex: Simulado Prévio de Circuitos Lógicos")
                disciplina = st.text_input("Componente Curricular / Disciplina", placeholder="Ex: Engenharia de Software")
                tema = st.text_input("Assunto Específico / Tema", placeholder="Ex: Arquitetura Monolítica")
                
                btn_criar = st.form_submit_button("Registrar e Ativar Sala", use_container_width=True)
                
                if btn_criar:
                    if not titulo.strip():
                        st.error("O título do quiz é obrigatório para abrir a sala.")
                    else:
                        with st.spinner("Ativando sala..."):
                            resultado = criar_quiz(titulo, user_id, disciplina, tema)
                            if resultado and resultado.get("sucesso") == True:
                                st.success(f"✅ {resultado.get('mensagem')}")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(resultado.get("mensagem", "Erro operacional ao tentar abrir sala."))

    with aba_lista:
        st.subheader("Salas de Quiz Registradas")
        
        col_atualizar, _ = st.columns([1, 3])
        with col_atualizar:
            if st.button("🔄 Sincronizar Salas", use_container_width=True):
                st.rerun()
                
        quizzes = listar_quizzes_do_banco()

        if not quizzes:
            st.info("Nenhuma sessão de quiz síncrono localizada no momento.")
            return

        for q in quizzes:
            q_id = q.get("id")
            status = str(q.get("status", "criado")).strip().lower()
            tema_txt = q.get("tema") or "Geral"
            
            autor_objeto = q.get("usuarios")
            if isinstance(autor_objeto, dict):
                autor = autor_objeto.get("nome", "Professor")
            else:
                autor = usuario.get("nome", "Professor") if tipo in ("professor", "admin") else "Docente"
            
            if status == "em_andamento":
                cor_status = "#2a9d8f"
                txt_status = "Em Andamento 🟢"
            elif status == "finalizado":
                cor_status = "#e63946"
                txt_status = "Finalizado 🛑"
            else:
                cor_status = "#00b4d8"
                txt_status = "Aguardando Início ⏱️"

            with st.container(border=True):
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0; color:#1b3a5c;">{q.get('titulo')}</h4>
                    <span style="background:{cor_status}; color:#fff; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600;">{txt_status}</span>
                </div>
                <p style="margin:5px 0 0; font-size:12px; color:#555;">
                    👤 Responsável: <strong>{autor}</strong> | 📌 Tema: <code>{tema_txt}</code>
                </p>
                """, unsafe_allow_html=True)
                
                if tipo in ("professor", "admin"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([2, 2, 1]) # ✅ Mudado para 3 colunas para acomodar o excluir
                    
                    with col1:
                        if status == "criado":
                            if st.button("▶️ Iniciar Quiz", key=f"start_{q_id}", type="primary", use_container_width=True):
                                alterar_status_quiz(q_id, "em_andamento")
                                st.toast("🚀 A sala do Quiz foi aberta para os alunos!")
                                time.sleep(0.3)
                                st.rerun()
                        elif status == "em_andamento":
                            if st.button("🛑 Finalizar / Encerrar", key=f"stop_{q_id}", use_container_width=True):
                                alterar_status_quiz(q_id, "finalizado")
                                st.toast("Sala de quiz encerrada oficialmente.")
                                time.sleep(0.3)
                                st.rerun()
                        else:
                            st.button("🔒 Finalizado", key=f"ended_{q_id}", disabled=True, use_container_width=True)
                            
                    with col2:
                        if st.button("📊 Ver Telão de Líderes", key=f"rank_{q_id}", use_container_width=True, disabled=(status == "criado")):
                            st.session_state.quiz_ranking_id = q_id
                            st.session_state.pagina = "quiz_ranking_global"
                            st.rerun()

                    # ✅ NOVO: Botão de exclusão com popover de confirmação de segurança
                    with col3:
                        with st.popover("🗑️ Deletar", use_container_width=True):
                            st.warning("Excluir este quiz permanentemente?")
                            if st.button("Sim, apagar", key=f"del_quiz_{q_id}", type="primary", use_container_width=True):
                                if deletar_quiz(q_id):
                                    st.toast("Quiz removido com sucesso!")
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error("Erro ao deletar.")
                    
                    if status != "finalizado":
                        with st.expander("📢 Mapeamento de Links & QR Code para Alunos", expanded=False):
                            exibir_painel_compartilhamento(tipo_sala="quiz", sala_id=q_id)
                
                else:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if status == "em_andamento":
                        if st.button("🎯 Ingressar na Sala e Responder", key=f"play_{q_id}", type="primary", use_container_width=True):
                            st.session_state.quiz_ativo_id = q_id
                            st.session_state.pagina = "quiz_rodada"
                            st.rerun()
                    elif status == "finalizado":
                        st.button("🔒 Quiz Encerrado", key=f"play_{q_id}", use_container_width=True, disabled=True)
                    else:
                        st.button("⏳ Aguardando Professor Iniciar...", key=f"play_{q_id}", use_container_width=True, disabled=True)