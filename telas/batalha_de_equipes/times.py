import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import (
    criar_time, 
    listar_times, 
    entrar_no_time, 
    listar_membros_time,
    aluno_tem_time
)

def tela_batalha_times():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho(
        "🏢 Central de Equipes e Times",
        "Crie uma nova equipa ou junte-se a um grupo ativo para libertar o seu acesso à Arena Ao Vivo"
    )
    
    # ------------------------------------------------------------------------
    # PAINEL EXCLUSIVO: ALUNO (CRIAR OU PARTICIPAR DE TIMES)
    # ------------------------------------------------------------------------
    if tipo_usuario == "aluno":
        st.markdown("### 🛠️ Suas Opções de Alocação")
        
        # Verifica em tempo real se o estudante já possui um time vinculado
        possui_time = aluno_tem_time(usuario_id)
        
        if possui_time:
            st.success("✅ Você já está devidamente alocado em uma equipe! Aguarde as instruções do professor na sala.")
        else:
            col_criar, col_entrar = st.columns(2)
            
            with col_criar:
                with st.container(border=True):
                    st.markdown("#### ✨ Criar Nova Equipa")
                    st.caption("Seja o fundador de um novo clã. Escolha um nome imponente e convide os seus colegas.")
                    
                    nome_novo_time = st.text_input("Nome da Equipa:", key="input_nome_novo_time")
                    
                    if st.button("🔥 Fundar Equipa", type="primary", use_container_width=True):
                        if not nome_novo_time.strip():
                            st.error("🛑 Digite um nome válido para o time.")
                        else:
                            sucesso = criar_time(nome_novo_time)
                            if sucesso:
                                st.toast(f"🎉 Equipa '{nome_novo_time}' criada com sucesso!", icon="🚀")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao criar time. O nome pode já estar em uso.")
            
            with col_entrar:
                with st.container(border=True):
                    st.markdown("#### 🚪 Entrar em Equipa Ativa")
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
                                st.toast(f"✅ Você agora faz parte do time {time_selecionado['nome']}!", icon="🤝")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Falha ao entrar no time. Verifique se a equipa já está cheia.")

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()

    # ------------------------------------------------------------------------
    # PAINEL GLOBAL: MURAL VISUAL DE TIMES E INTEGRANTES (VISÍVEL A TODOS)
    # ------------------------------------------------------------------------
    st.markdown("### 📊 Mural das Equipes Registadas")
    st.caption("Confira abaixo a composição atual de cada time do ecossistema:")
    
    todos_times = listar_times()
    
    if not todos_times:
        st.info("Nenhuma equipa registada no sistema até ao momento.")
    else:
        # Renderiza os times em formato de Grid de Cards de 2 colunas
        for i in range(0, len(todos_times), 2):
            cols_grid = st.columns(2)
            
            # Card do Time 1 da Linha
            with cols_grid[0]:
                t1 = todos_times[i]
                with st.container(border=True):
                    st.markdown(f"#### 🏢 {t1['nome']}")
                    membros_t1 = listar_membros_time(t1["id"])
                    
                    # CORRIGIDO: Remoção do operador walrus para compatibilidade estrita
                    if not membros_t1:
                        st.caption("Empty 👥 — Equipa sem integrantes alocados.")
                    else:
                        for m in membros_t1:
                            st.markdown(f"• **{m['nome']}** ({m['email']})")
            
            # Card do Time 2 da Linha (se houver)
            if i + 1 < len(todos_times):
                with cols_grid[1]:
                    t2 = todos_times[i + 1]
                    with st.container(border=True):
                        st.markdown(f"#### 🏢 {t2['nome']}")
                        membros_t2 = listar_membros_time(t2["id"])
                        
                        # CORRIGIDO: Remoção do operador walrus e ajuste do loop interno
                        if not membros_t2:
                            st.caption("Empty 👥 — Equipa sem integrantes alocados.")
                        else:
                            for m in membros_t2:
                                st.markdown(f"• **{m['nome']}** ({m['email']})")

    # Botão universal de retorno
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⬅️ Voltar para a Arena de Batalhas", use_container_width=True, key="btn_back_times_to_arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()