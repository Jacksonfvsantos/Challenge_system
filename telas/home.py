import streamlit as st
from services.desafio_service import listar_desafios
from services.auth_service import excluir_conta_usuario
from utils.estilo import aplicar_estilo, cabecalho

def tela_home():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    nome_usuario = usuario.get("nome", "Usuário")
    
    cabecalho(
        f"Olá, {nome_usuario}!",
        "Bem-vindo ao painel do Challenge System. Veja as novidades abaixo."
    )
    
    st.subheader("Desafios em Destaque")
    try:
        desafios = listar_desafios()
    except Exception:
        desafios = []
        
    if not desafios:
        st.info("Nenhum desafio listado no momento.")
    else:
        for desafio in desafios[:3]:  
            with st.container(border=True):
                st.markdown(f"### {desafio.get('titulo', 'Sem Título')}")
                st.write(desafio.get("descricao", "Sem descrição disponível."))
                
                col1, col2 = st.columns(2)
                with col1:
                    nivel = desafio.get("nivel_dificuldade") or desafio.get("nivel") or "Não informado"
                    st.caption(f"**Nível:** {nivel}")
                with col2:
                    prazo = desafio.get("data_limite", "Sem prazo")
                    st.caption(f"**Prazo final:** {prazo}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    
    with st.expander("⚙️ Configurações e Gerenciamento da Conta"):
        st.subheader("Privacidade e Inscrições")
        st.markdown("**Gerenciar Participações**")
        st.caption("Clique abaixo para se desligar de eventos ou desafios pendentes no sistema.")
        
        if st.button("❌ Cancelar Minhas Inscrições Realizadas", use_container_width=True):
            st.success("✅ Todas as suas inscrições em desafios ativos foram canceladas com sucesso!")
            st.rerun()
            
        st.divider()
        st.markdown("<span style='color: #ff4b4b; font-weight: bold;'>Zona de Perigo</span>", unsafe_allow_html=True)
        st.caption("A exclusão de conta é definitiva e removerá permanentemente seu histórico e suas pontuações.")
        
        confirmar_exclusao = st.checkbox("Estou ciente de que esta ação é irreversível e desejo apagar minha conta permanentemente.")
        if st.button("⚠️ Solicitar Remoção Permanente da Conta", type="primary", use_container_width=True):
            if not confirmar_exclusao:
                st.warning("Por favor, marque a caixa de confirmação para poder prosseguir.")
            else:
                sucesso = excluir_conta_usuario(usuario.get("id"))
                if sucesso:
                    st.success("🎉 Sua conta foi removida com sucesso. Redirecionando...")
                    st.session_state.usuario_logado = None
                    st.session_state.pagina = "login"
                    st.rerun()
                else:
                    st.error("Não foi possível processar a exclusão. Verifique sua conexão com o banco.")