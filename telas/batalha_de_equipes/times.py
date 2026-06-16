import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_de_equipes_service import (
    criar_time, 
    aluno_tem_time, 
    entrar_no_time, 
    listar_times, 
    editar_time, 
    deletar_time
)

def tela_batalha_times():
    aplicar_estilo()
    
    # 1. Identificação do Usuário e Perfil
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho(
        "👥 Gestão e Fundação de Equipes", 
        "Cadastre novos times na arena corporativa ou gerencie as nomenclaturas existentes."
    )
    
    # Botão de retorno seguro para o painel principal da Arena
    if st.button("⬅️ Voltar para a Arena", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()
        
    st.divider()
    
    # 2. BLOCO: CRIAR / FUNDAR NOVO TIME
    st.markdown("### ✨ Criar Novo Time")
    
    # Validação rigorosa de negócio: Aluno só cria se estiver "sem teto" (sem time)
    ja_tem_time = aluno_tem_time(usuario_id) if tipo == "aluno" else False
    
    with st.container(border=True):
        nome_do_time = st.text_input("Nome da nova equipe:", placeholder="Ex: Computaloucos")
        
        if ja_tem_time:
            st.warning("🔒 Ação bloqueada: Você já faz parte de uma equipe ativa e não pode fundar outra.")
            btn_gravar = st.button("Gravar e Ativar Equipe", use_container_width=True, disabled=True)
        else:
            btn_gravar = st.button("Gravar e Ativar Equipe", use_container_width=True)
            
        if btn_gravar and not ja_tem_time:
            if not nome_do_time.strip():
                st.error("Por favor, insira um nome válido e preenchido para a equipe.")
            else:
                # Gravação direta no Supabase via Service unificado
                sucesso = criar_time(nome_do_time)
                if sucesso:
                    st.success(f"✅ Equipe '{nome_do_time.strip()}' cadastrada no servidor com sucesso!")
                    
                    # Automação de UX para o Aluno: vira membro instantaneamente do time que criou
                    if tipo == "aluno":
                        times_atualizados = listar_times()
                        time_criado = next(
                            (t for t in times_atualizados if t.get("nome", "").lower() == nome_do_time.strip().lower()), 
                            None
                        )
                        if time_criado:
                            entrar_no_time(time_criado["id"], usuario_id)
                            st.toast("Você foi vinculado automaticamente como membro fundador!")
                            
                    st.rerun()
                else:
                    st.error("Erro interno ao registrar o time. Certifique-se de que este nome já não esteja em uso.")

    st.divider()
    
    # 3. BLOCO: LISTAGEM E AUDITORIA DE TIMES EXISTENTES
    st.markdown("### 📋 Equipes Registradas no Sistema")
    
    times = listar_times()
    
    if not times:
        st.info("Nenhuma equipe foi localizada no banco de dados até o momento.")
        return

    for idx, t in enumerate(times):
        time_id_limpo = str(t.get("id")).strip()
        nome_atual = t.get("nome", "Sem Nome")
        
        with st.container(border=True):
            # Layout dinâmico: Professor ganha painel de modificação, Aluno apenas visualiza
            if tipo in ("professor", "admin"):
                col_txt, col_btn_edit, col_btn_del = st.columns([3, 1, 1])
                
                with col_txt:
                    st.markdown(f"**Equipe {idx + 1}:** `{nome_atual}`")
                    st.caption(f"ID Ref: {time_id_limpo}")
                
                with col_btn_edit:
                    # Expander embutido para edição in-place limpa
                    with st.popover("📝 Alterar", use_container_width=True):
                        st.markdown("**Modificar Nomenclatura**")
                        novo_nome_input = st.text_input("Novo nome:", value=nome_atual, key=f"edit_input_{time_id_limpo}")
                        if st.button("Salvar Mudança", key=f"btn_save_{time_id_limpo}", use_container_width=True):
                            if novo_nome_input.strip() and editar_time(time_id_limpo, novo_nome_input):
                                st.success("Nome atualizado!")
                                st.rerun()
                            else:
                                st.error("Falha ao atualizar.")
                                
                with col_btn_del:
                    if st.button("🗑️ Excluir", key=f"btn_del_{time_id_limpo}", type="primary", use_container_width=True):
                        if deletar_time(time_id_limpo):
                            st.success("Equipe removida!")
                            st.rerun()
                        else:
                            st.error("🔒 Bloqueado: Limpe os integrantes vinculados a este time antes de excluí-lo.")
            else:
                # Visão simples e limpa do Aluno
                st.markdown(f"🏅 **Equipe {idx + 1}:** {nome_atual}")