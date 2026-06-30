import streamlit as st
import pandas as pd
import time
from utils.estilo import aplicar_estilo, cabecalho
from database.conexao import supabase
from services.quiz_ao_vivo_service import criar_quiz, deletar_quiz
from services.cadastro_quiz_service import cadastrar_pergunta_completa
from utils.compartilhamento import exibir_painel_compartilhamento

def listar_quizzes_do_banco():
    try:
        res = supabase.table("quizzes").select("*, usuarios(nome)").order("data_criacao", desc=True).execute()
        return res.data or []
    except Exception:
        try:
            res = supabase.table("quizzes").select("*").order("data_criacao", desc=True).execute()
            return res.data or []
        except Exception:
            return []

def alterar_status_quiz(quiz_id, novo_status):
    try:
        res = supabase.table("quizzes").update({"status": novo_status}).eq("id", quiz_id).execute()
        return bool(res.data)
    except Exception as e:
        st.error(f"❌ Erro estrutural no Supabase: {e}")
        return False

def puxar_perguntas_cadastradas(quiz_id):
    try:
        res = supabase.table("perguntas_quiz").select("*").eq("quiz_id", quiz_id).order("ordem").execute()
        return res.data or []
    except Exception:
        return []

def tela_quiz_ao_vivo():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()
    user_id = usuario.get("id")

    cabecalho(
        "🎮 Quiz Acadêmico ao Vivo",
        "Participe ou gerencie sessões síncronas de perguntas e respostas em tempo real"
    )

    if tipo in ("professor", "admin"):
        aba_gestao, aba_caderno, aba_lista = st.tabs([
            "✨ Criar Novo Quiz", 
            "📝 Caderno de Questões", 
            "📊 Painel de Controle Síncrono"
        ])
    else:
        aba_lista, = st.tabs(["🎮 Quizzes Disponíveis"])

    if tipo in ("professor", "admin"):
        with aba_gestao:
            st.subheader("Configurar Nova Sessão de Quiz")
            titulo = st.text_input("Título do Quiz", placeholder="Ex: Simulado Prévio de Circuitos Lógicos", key="input_create_title")
            disciplina = st.text_input("Componente Curricular / Disciplina", placeholder="Ex: Engenharia de Software", key="input_create_disc")
            tema = st.text_input("Assunto Específico / Tema", placeholder="Ex: Arquitetura Monolítica", key="input_create_theme")
            
            if st.button("Registrar e Ativar Sala", use_container_width=True, type="primary", key="btn_execute_create_quiz"):
                if not titulo.strip():
                    st.error("O título do quiz é obrigatório para abrir a sala.")
                else:
                    with st.spinner("Ativando sala..."):
                        resultado = criar_quiz(titulo, user_id, disciplina, tema)
                        if resultado and resultado.get("sucesso"):
                            st.success("Sala de Quiz ativada com sucesso! Acesse o Caderno de Questões.")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Erro ao tentar abrir sala.")

        with aba_caderno:
            st.subheader("Alimentar Banco de Perguntas")
            quizzes_disponiveis = listar_quizzes_do_banco()
            if not quizzes_disponiveis:
                st.info("💡 Você precisa criar uma Sala de Quiz primeiro na aba ao lado.")
            else:
                opcoes_quiz = {q["titulo"]: q["id"] for q in quizzes_disponiveis}
                quiz_selecionado_titulo = st.selectbox("Escolha o Quiz que deseja alimentar:", list(opcoes_quiz.keys()), key="select_quiz_caderno")
                quiz_id_caderno = opcoes_quiz[quiz_selecionado_titulo]

                perguntas_atuais = puxar_perguntas_cadastradas(quiz_id_caderno)
                st.caption(f"📊 Este quiz possui atualmente **{len(perguntas_atuais)}** pergunta(s) salva(s).")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("▶️ Iniciar Jogatina Deste Quiz Agora", type="primary", key="start_from_caderno", use_container_width=True):
                        alterar_status_quiz(quiz_id_caderno, "ativo")
                        st.session_state.quiz_ativo_id = quiz_id_caderno
                        st.session_state.pagina = "quiz_rodada"
                        st.rerun()
                with col_btn2:
                    if st.button("🔄 Sincronizar e Ir para o Painel Geral", key="go_to_panel_caderno", use_container_width=True):
                        st.rerun()

                st.markdown("---")
                enunciado = st.text_area("Enunciado da Pergunta", key="input_q_enunciado")
                tempo_limite = st.slider("Tempo Limite (Segundos)", min_value=10, max_value=120, value=30, step=5, key="input_q_timer")
                alt_a = st.text_input("Alternativa A", key="input_q_alta")
                alt_b = st.text_input("Alternativa B", key="input_q_altb")
                alt_c = st.text_input("Alternativa C", key="input_q_altc")
                alt_d = st.text_input("Alternativa D", key="input_q_altd")
                
                mapeamento_letras = {"Alternativa A": 0, "Alternativa B": 1, "Alternativa C": 2, "Alternativa D": 3}
                correta_letra = st.radio("Selecione a correta:", list(mapeamento_letras.keys()), horizontal=True, key="input_q_correct")
                
                if st.button("💾 Salvar Pergunta", use_container_width=True, type="secondary", key="btn_save_q_manual"):
                    if not enunciado.strip() or not all([alt_a.strip(), alt_b.strip(), alt_c.strip(), alt_d.strip()]):
                        st.error("Preencha todos os campos antes de realizar o envio.")
                    else:
                        with st.spinner("Salvando questão..."):
                            res = cadastrar_pergunta_completa(quiz_id_caderno, enunciado, tempo_limite, [alt_a, alt_b, alt_c, alt_d], mapeamento_letras[correta_letra])
                            if res["sucesso"]:
                                st.success("Questão salva com sucesso!")
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.error("Erro ao salvar questão.")

                if perguntas_atuais:
                    with st.expander("👁️ Ver Questões Salvas", expanded=False):
                        for p in perguntas_atuais:
                            st.markdown(f"**Q{p['ordem']}. {p.get('enunciado') or p.get('texto')}** *({p.get('tempo_limite_segundos')}s)*")

    with aba_lista:
        st.subheader("Salas de Quiz Registradas")
        if st.button("🔄 Sincronizar Listagem de Salas", key="btn_sync_manual_salas", use_container_width=True):
            st.rerun()
                
        quizzes = listar_quizzes_do_banco()
        if not quizzes:
            st.info("Nenhuma sessão de quiz síncrono localizada.")
            return

        for q in quizzes:
            q_id = q.get("id")
            status = str(q.get("status", "criado")).strip().lower()
            tema_txt = q.get("tema") or "Geral"
            autor_objeto = q.get("usuarios")
            autor = autor_objeto.get("nome", "Professor") if isinstance(autor_objeto, dict) else "Professor Responsável"

            if status in ("em_andamento", "andamento", "ativo"):
                cor_status, txt_status = "#2a9d8f", "Em Andamento 🟢"
            elif status == "finalizado":
                cor_status, txt_status = "#e63946", "Finalizado 🛑"
            else:
                cor_status, txt_status = "#00b4d8", "Aguardando Início ⏱️"

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
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        if status == "criado":
                            if st.button("▶️ Iniciar Quiz", key=f"btn_start_quiz_{q_id}", type="primary", use_container_width=True):
                                if alterar_status_quiz(q_id, "ativo"):
                                    st.session_state.quiz_ativo_id = q_id
                                    st.session_state.pagina = "quiz_rodada"
                                    st.rerun()
                        elif status in ("em_andamento", "andamento", "ativo"):
                            if st.button("🎯 Ir p/ Painel da Rodada", key=f"btn_go_curr_{q_id}", type="primary", use_container_width=True):
                                st.session_state.quiz_ativo_id = q_id
                                st.session_state.pagina = "quiz_rodada"
                                st.rerun()
                        else:
                            st.button("🔒 Finalizado", key=f"btn_ended_static_{q_id}", disabled=True, use_container_width=True)
                            
                    with col2:
                        if st.button("📊 Ver Telão de Líderes", key=f"btn_rank_view_{q_id}", use_container_width=True, disabled=(status == "criado")):
                            st.session_state.quiz_ranking_id = q_id
                            st.session_state.pagina = "quiz_ranking_global"
                            st.rerun()

                    with col3:
                        with st.popover("🗑️ Deletar", use_container_width=True, key=f"popover_del_{q_id}"):
                            st.warning("Excluir permanentemente?")
                            if st.button("Sim, apagar", key=f"btn_confirm_del_action_{q_id}", type="primary", use_container_width=True):
                                if deletar_quiz(q_id):
                                    st.toast("Quiz removido com sucesso!")
                                    time.sleep(0.4)
                                    st.rerun()
                    
                    if status != "finalizado":
                        with st.expander("📢 Mapeamento de Links & QR Code para Alunos", expanded=False):
                            exibir_painel_compartilhamento(tipo_sala="quiz", sala_id=q_id)
                else:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if status in ("em_andamento", "andamento", "ativo"):
                        if st.button("🎯 Ingressar na Sala e Responder", key=f"btn_student_join_play_{q_id}", type="primary", use_container_width=True):
                            st.session_state.quiz_ativo_id = q_id
                            st.session_state.pagina = "quiz_rodada"
                            st.rerun()
                    elif status == "finalizado":
                        st.button("🔒 Quiz Encerrado", key=f"btn_disabled_ended_{q_id}", use_container_width=True, disabled=True)
                    else:
                        st.button("⏳ Aguardando Professor Iniciar...", key=f"btn_disabled_wait_{q_id}", use_container_width=True, disabled=True)