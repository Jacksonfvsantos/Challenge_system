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
    aceitar_membro,           
    verificar_capitao,        
    listar_membros_pendentes,
    obter_status_membro,      # <-- Nova Importação
    recusar_membro            # <-- Nova Importação
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
            # 1. Busca o status real do aluno (Pendente ou Aceito)
            status_membro = obter_status_membro(usuario_id)
            times_do_aluno = obter_time_do_usuario(usuario_id)
            time_id = times_do_aluno[0] if times_do_aluno else None
            
            # --- FLUXO 1: ALUNO EM ESPERA ---
            if status_membro == "pendente":
                st.warning("⏳ **Solicitação em análise!** Você solicitou entrada nesta equipe e está aguardando a aprovação do Capitão.")
                st.caption("Enquanto o Capitão não aprovar, você não terá acesso à Arena Síncrona pela equipe.")
                
                if st.button("❌ Cancelar Solicitação", type="secondary"):
                    if recusar_membro(usuario_id):
                        st.toast("Solicitação cancelada com sucesso.")
                        time.sleep(1)
                        st.rerun()
                        
            # --- FLUXO 2: ALUNO ACEITO OFICIALMENTE ---
            elif status_membro == "aceito":
                st.success("✅ Você já está devidamente alocado em uma equipe oficial! Aguarde as instruções do professor na sala.")
                
                # --- PAINEL EXCLUSIVO DO CAPITÃO ---
                if verificar_capitao(usuario_id) and time_id:
                    with st.expander("👑 Painel do Capitão - Gerenciar Solicitações", expanded=True):
                        st.caption("Aprove ou recuse os pedidos de entrada de outros alunos no seu time.")
                        pendentes = listar_membros_pendentes(time_id)
                        
                        if not pendentes:
                            st.info("Nenhuma solicitação de entrada pendente no momento.")
                        else:
                            st.warning(f"Você tem {len(pendentes)} solicitação(ões) pendente(s)!")
                            for p in pendentes:
                                col_info, col_acc, col_rec = st.columns([2, 1, 1])
                                col_info.markdown(f"👤 **{p['nome']}**")
                                
                                # Botão de Aceitar
                                if col_acc.button("✅ Aceitar", key=f"acc_{p['id']}", type="primary", use_container_width=True):
                                    if aceitar_membro(p['id']):
                                        st.toast(f"✅ {p['nome']} agora é da equipe!")
                                        time.sleep(1)
                                        st.rerun()
                                        
                                # Botão de Recusar (Novo!)
                                if col_rec.button("❌ Recusar", key=f"rec_{p['id']}", type="secondary", use_container_width=True):
                                    if recusar_membro(p['id']):
                                        st.toast(f"❌ Solicitação de {p['nome']} foi recusada.")
                                        time.sleep(1)
                                        st.rerun()
                
                st.write("") 
                
                # O botão de Sair da Equipe
                if st.button("🚪 Sair da minha equipe atual", type="secondary"):
                    # Utilizando a função recusar_membro para remover o próprio vínculo
                    if recusar_membro(usuario_id):
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

    # --- MURAL DAS EQUIPES ---
    st.markdown("### 📊 Mural das Equipes Oficiais")
    st.caption("Confira abaixo a composição atual (membros aceitos) de cada time do ecossistema:")
    
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
                    # A função listar_membros_time agora traz APENAS os membros aceitos
                    membros_t1 = listar_membros_time(t1["id"]) 
                    
                    if not membros_t1:
                        st.caption("Empty 👥 — Sem membros confirmados.")
                    else:
                        for m in membros_t1:
                            st.markdown(f"• **{m['nome']}**")
            
            if i + 1 < len(todos_times):
                with cols_grid[1]:
                    t2 = todos_times[i + 1]
                    with st.container(border=True):
                        st.markdown(f"#### 🏢 {t2['nome']}")
                        membros_t2 = listar_membros_time(t2["id"])
                        
                        if not membros_t2:
                            st.caption("Empty 👥 — Sem membros confirmados.")
                        else:
                            for m in membros_t2:
                                st.markdown(f"• **{m['nome']}**")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Voltar para a Arena de Batalhas", use_container_width=True, key="btn_back_times_to_arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()