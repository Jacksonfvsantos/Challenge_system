import streamlit as st
from services.notificacao_service import listar_notificacoes_usuario, marcar_notificacao_como_lida
from utils.estilo import aplicar_estilo, cabecalho

def tela_notificacoes_mini_provas():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")

    cabecalho("🔔 Central de Notificações", "Acompanhe seus avisos, prazos e atualizações do Challenge System")

    if not usuario_id:
        st.error("Sessão de usuário inválida ou expirada.")
        return

    notificacoes = listar_notificacoes_usuario(usuario_id)

    if not notificacoes:
        st.info("💡 Você não tem nenhuma notificação pendente ou lida no momento.")
    else:
        for n in notificacoes:
            tipo_card = "⚠️" if not n["lida"] else "🔹"
            cor_borda = "#00b4d8" if not n["lida"] else "#cbd5e1"
            fundo = "#f0f9ff" if not n["lida"] else "#ffffff"

            with st.container(border=True):
                st.markdown(f"""
                <div style="background: {fundo}; border-left: 4px solid {cor_borda}; padding: 10px; border-radius: 4px;">
                    <strong style="color: #1b3a5c;">{tipo_card} {n['titulo']}</strong><br>
                    <span style="color: #334155; font-size: 14px;">{n['mensagem']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if not n["lida"]:
                    st.write("")
                    if st.button("Marcar como lida", key=f"read_{n['id']}", use_container_width=True):
                        if marcar_notificacao_como_lida(n["id"]):
                            st.rerun()

    st.divider()
    if st.button("⬅️ Voltar para o Painel Geral", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()