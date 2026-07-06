import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import (
    criar_time, 
    listar_times, 
    entrar_no_time, 
    listar_membros_time,
    aluno_tem_time,
    obter_time_do_usuario,
    remover_aluno,
    aceitar_membro,           # <-- Importação adicionada
    verificar_capitao,        # <-- Importação adicionada
    listar_membros_pendentes  # <-- Importação adicionada
)

def tela_batalha_times():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho(
        "🏢 Central de Equipes e Times",
        "Crie uma nova equipe ou junte-se a um grupo ativo para liberar o seu acesso à Arena Ao Vivo"
    )
    
    # ⚠️ ATENÇÃO: Esta seção inteira só aparece para ALUNOS
    if tipo_usuario == "aluno":
        st.markdown("### 🛠️ Suas Opções de Alocação")
        possui_time = aluno_tem_time(usuario_id)
        
        if possui_time:
            st.success("✅ Você já está devidamente alocado em uma equipe! Aguarde as instruções do professor na sala.")
            
            times_do_aluno = obter_time_do_usuario(usuario_id)
            if times_do_aluno and times_do_aluno[0]:
                time_id = times_do_aluno[0]
                
                # --- PAINEL EXCLUSIVO DO CAPITÃO ---
                if verificar_capitao(usuario_id):
                    with st.expander("👑 Painel do Capitão - Gerenciar Solicitações", expanded=True):
                        st.caption("Aprove ou ignore os pedidos de entrada de outros alunos no seu time.")
                        pendentes = listar_membros_pendentes(time_id)
                        
                        if not pendentes:
                            st.info("Nenhuma solicitação de entrada pendente no momento.")
                        else:
                            st.warning(f"Você tem {len(pendentes)} solicitação(ões) pendente(s)!")
                            for p in pendentes:
                                col_info, col_btn = st.columns([3, 1])
                                col_info.markdown(f"👤 **{p['nome']}** ({p['email']})")
                                if col_btn.button("Aceitar", key=f"acc_{p['id']}", type="primary", use_container_width=True):
                                    if aceitar_membro(p['id']):
                                        st.toast(f"✅ {p['nome']} foi aceito na equipe!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Erro ao aceitar membro.")
                
            st.write("") # Espaço em branco
            
            # --- O BOTÃO DE SAIR DA EQUIPE ESTÁ AQUI ---
            if st.button("🚪 Sair da minha equipe atual", type="secondary"):
                if times_do_aluno and times_do_aluno[0]:
                    if remover_aluno(time_id, usuario_id):
                        st.toast("Você saiu da equipe com sucesso.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erro ao sair da equipe.")
                        
        else:
            col_criar, col_entrar = st.columns(2)
            
            with col_criar:
                with st.container(border=True):
                    st.markdown("#### ✨ Criar Nova Equipe")
                    st.caption("Seja o fundador de um novo clã. Escolha um nome imponente e convide os seus colegas.")
                    
                    nome_novo_time = st.text_input("Nome da Equipe:", key="input_nome_novo_time")
                    
                    if st.button("🔥 Fundar Equipe", type="primary", use_container_width=True):
                        if not nome_novo_time.strip():
                            st.error("🛑 Digite um nome válido para o time.")
                        else:
                            # Correção: Agora passando o usuario_id para registrar o capitão
                            sucesso = criar_time(nome_novo_time, usuario_id) 
                            if sucesso:
                                st.toast(f"🎉 Equipe '{nome_novo_time}' criada com sucesso!", icon="🚀")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao criar time. O nome pode já estar em uso.")
            
            with col_entrar:
                with st.container(border=True):
                    st.markdown("#### 🚪 Entrar em Equipe Ativa")
                    st.caption("Prefere juntar-se a um projeto existente? Selecione abaixo uma das equipas que possuem vagas livres.")
                    
                    times_disponiveis = listar_times()
                    
                    if not times_disponiveis:
                        st.info("Nenhum time disponível para ingresso no momento.")
                    else:
                        time_selecionado = st.selectbox(
                            "Escolha o Time:",
                            options=times_disponiveis,
                            format_func=lambda x: str(x["nome"]).strip(),
                            key="select_ingresso_time_aluno"
                        )
                        
                        if st.button("📥 Solicitar Entrada", use_container_width=True):
                            if entrar_no_time(time_selecionado["id"], usuario_id):
                                st.toast(f"⏳ Solicitação enviada! Aguarde o capitão do time {time_selecionado['nome']} aprovar.", icon="🤝")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("❌ Falha ao solicitar entrada. Verifique se você já solicitou antes.")

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()

    # Esta seção debaixo (Mural) aparece para TODO MUNDO (Aluno e Professor)
    st.markdown("### 📊 Mural das Equipes Registadas")
    st.caption("Confira abaixo a composição atual de cada time do ecossistema:")
    
    todos_times = listar_times()
    
    if not todos_times:
        st.info("Nenhuma equipa registada no sistema até ao momento.")
    else:
        for i in range(0, len(todos_times), 2):
            cols_grid = st.columns(2)
            
            with cols_grid[0]:
                t1 = todos_times[i]
                with st.container(border=True):
                    st.markdown(f"#### 🏢 {t1['nome']}")
                    membros_t1 = listar_membros_time(t1["id"])
                    
                    if not membros_t1:
                        st.caption("Empty 👥 — Equipa sem integrantes alocados.")
                    else:
                        for m in membros_t1:
                            st.markdown(f"• **{m['nome']}** ({m['email']})")
            
            if i + 1 < len(todos_times):
                with cols_grid[1]:
                    t2 = todos_times[i + 1]
                    with st.container(border=True):
                        st.markdown(f"#### 🏢 {t2['nome']}")
                        membros_t2 = listar_membros_time(t2["id"])
                        
                        if not membros_t2:
                            st.caption("Empty 👥 — Equipa sem integrantes alocados.")
                        else:
                            for m in membros_t2:
                                st.markdown(f"• **{m['nome']}** ({m['email']})")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Voltar para a Arena de Batalhas", use_container_width=True, key="btn_back_times_to_arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()