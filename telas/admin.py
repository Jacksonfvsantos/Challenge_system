import streamlit as st
import pandas as pd
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.auth_service import listar_usuarios, alterar_privilegio_usuario, excluir_conta_usuario

def tela_admin():
    aplicar_estilo()
    
    usuario_logado = st.session_state.get("usuario_logado", {})
    
    # Trava de Segurança: Expulsa quem não for admin
    if str(usuario_logado.get("tipo_usuario", "")).lower() != "admin":
        st.error("🛑 Acesso Negado. Esta área é restrita para administradores do sistema.")
        return

    cabecalho("🛡️ Painel de Administração", "Gestão centralizada de usuários, perfis e governança do ecossistema")

    st.markdown("### 👥 Gestão de Usuários")
    usuarios = listar_usuarios()

    if not usuarios:
        st.info("Nenhum usuário encontrado.")
        return

    # Tabela visual para o ADM conferir quem é quem
    df_users = pd.DataFrame(usuarios)
    st.dataframe(
        df_users[["nome", "email", "tipo_usuario"]].rename(columns={"nome": "Nome", "email": "E-mail", "tipo_usuario": "Perfil"}), 
        use_container_width=True, 
        hide_index=True
    )

    st.divider()

    # Controles de edição
    col_edit, col_del = st.columns(2)

    # Cria um dicionário para o Selectbox (Nome + Email -> ID), excluindo o próprio ADM logado para evitar que ele se delete sem querer
    mapa_usuarios = {f"{u['nome']} ({u['email']})": str(u["id"]).strip() for u in usuarios if str(u["id"]) != str(usuario_logado.get("id"))}

    with col_edit:
        with st.container(border=True):
            st.markdown("#### 🔄 Promover / Rebaixar Perfil")
            if not mapa_usuarios:
                st.caption("Nenhum outro usuário disponível para edição.")
            else:
                user_selecionado = st.selectbox("Selecione o usuário:", list(mapa_usuarios.keys()), key="sb_edit_user")
                novo_perfil = st.selectbox("Novo perfil de acesso:", ["aluno", "professor", "admin"])

                if st.button("Atualizar Privilégio", type="primary", use_container_width=True):
                    if alterar_privilegio_usuario(mapa_usuarios[user_selecionado], novo_perfil):
                        st.success(f"Perfil de {user_selecionado.split(' ')[0]} atualizado para {novo_perfil.upper()}!")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Erro ao atualizar perfil.")

    with col_del:
        with st.container(border=True):
            st.markdown("#### ❌ Excluir Conta")
            st.caption("Atenção: Esta ação é irreversível e apaga os vínculos do usuário.")
            if not mapa_usuarios:
                st.caption("Nenhum outro usuário disponível para exclusão.")
            else:
                user_del = st.selectbox("Selecione o usuário para exclusão:", list(mapa_usuarios.keys()), key="sb_del_user")

                if st.button("Apagar Conta Definitivamente", type="secondary", use_container_width=True):
                    if excluir_conta_usuario(mapa_usuarios[user_del]):
                        st.success("Usuário removido do sistema.")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Erro ao excluir usuário. Ele pode estar travado como Capitão de uma equipe ativa.")