import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import listar_batalhas_ativas, cadastrar_nova_batalha

def tela_gerenciar_batalhas():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    
    cabecalho("🛠️ Gestão de Batalhas", "Administração de editais e monitoramento síncrono")

    aba_ativas, aba_nova = st.tabs(["🔥 Painel de Monitoramento Síncrono", "✨ Criar Novo Edital"])

    with aba_ativas:
        st.markdown("### 🔥 Painel de Monitoramento Síncrono")
        lista_ativas = listar_batalhas_ativas()

        if not lista_ativas:
            st.info("Não há nenhuma batalha ativa listada no momento.")
        else:
            for b in lista_ativas:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{b['titulo']}**")
                        st.caption(f"Time da vez: {b.get('times', {}).get('nome', 'N/A')}")
                    with col2:
                        if st.button("Encerrar Batalha", key=f"end_{b['id']}", use_container_width=True):
                            st.rerun()

    with aba_nova:
        st.markdown("### ✨ Abrir Novo Edital de Batalha")
        with st.form("form_nova_batalha"):
            titulo = st.text_input("Título da Batalha")
            descricao = st.text_area("Descrição / Regras")
            time_inicial = st.text_input("ID do Time Inicial (ex: UUID)")
            
            if st.form_submit_button("Publicar Edital"):
                if titulo:
                    resultado = cadastrar_nova_batalha(titulo, descricao, time_inicial)
                    if resultado.get("sucesso"):
                        st.success("Batalha criada com sucesso!")
                        st.rerun()
                    else:
                        st.error(resultado.get("mensagem", "Erro ao criar batalha."))
                else:
                    st.warning("O título é obrigatório.")

    if st.button("⬅️ Voltar"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()