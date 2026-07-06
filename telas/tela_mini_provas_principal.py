import streamlit as st
from services.mini_prova_service import listar_mini_provas
from utils.estilo import aplicar_estilo, cabecalho
from utils.compartilhamento import exibir_painel_compartilhamento

def tela_mini_provas():
    aplicar_estilo()
    # Título atualizado conforme nossa nova nomenclatura
    cabecalho("📝 Avaliações Modulares", "Realize as avaliações disponíveis e acompanhe seu desempenho")

    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    # Botão de criação exclusivo para professores/admin
    if tipo_usuario in ("professor", "admin"):
        if st.button("➕ Nova Mini-Prova", type="primary"): 
            st.session_state.pagina = "mini_provas_professor"
            st.rerun()
        st.divider()

    # Listagem de provas
    mini_provas = listar_mini_provas()
    provas_ativas = [p for p in mini_provas if p.get("status") == "Disponível"]

    st.markdown("### 📋 Provas Ativas")
    
    if not provas_ativas:
        st.info("Nenhuma avaliação disponível no momento.")
    else:
        for prova in provas_ativas:
            prova_id = prova.get("id")
            with st.container(border=True):
                # Informações da Prova
                st.markdown(f"""
                <strong style="color:#0d1b2a; font-size:16px;">{prova.get('titulo', 'Sem Título')}</strong><br>
                <span style="color:#555; font-size:13px;">{prova.get('descricao', 'Sem descrição.')}</span><br>
                <span style="color:#00b4d8; font-size:12px; font-weight:600;">
                    📝 {prova.get('quantidade_questoes', 0)} Questões &nbsp;|&nbsp; ⏱️ {prova.get('duracao_minutos', 0)} min
                </span>
                """, unsafe_allow_html=True)
                
                st.write("")
                
                # Ação para Alunos
                if tipo_usuario == "aluno":
                    if st.button("🚀 Iniciar Prova", key=f"start_{prova_id}", type="primary", use_container_width=True):
                        st.session_state.prova_ativa_id = prova_id
                        st.session_state.pagina = "realizar_mini_prova"
                        st.rerun()
                
                # Ações para Professores (Gestão e Compartilhamento)
                elif tipo_usuario in ("professor", "admin"):
                    col_edit, col_del = st.columns([3, 1])
                    
                    with col_edit:
                        if st.button("▶️ Entrar no Modo Professor", key=f"prof_{prova_id}", use_container_width=True):
                            st.session_state.prova_ativa_id = prova_id
                            st.session_state.pagina = "resultados_mini_provas"
                            st.rerun()
                            
                    with col_del:
                        if st.button("🗑️", key=f"del_{prova_id}", help="Excluir prova"):
                            from services.mini_prova_service import deletar_mini_prova
                            res = deletar_mini_prova(prova_id)
                            if res.get("sucesso"):
                                st.success("Prova excluída!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir.")
                    
                    # Painel de Compartilhamento (QR Code) - Requisito do Professor
                    with st.expander("📡 Painel de Compartilhamento (QR Code / Link)"):
                        exibir_painel_compartilhamento("mini_prova", prova_id)