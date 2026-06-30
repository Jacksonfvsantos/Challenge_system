import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho, formatar_titulo_aba, formatar_legenda_instrucao
from services.batalha_service import listar_batalhas_ativas, cadastrar_nova_batalha

def tela_gerenciar_batalhas():
    aplicar_estilo()
    cabecalho("Gestão de Batalhas", "Administração de editais e monitoramento síncrono")

    aba_ativas, aba_nova = st.tabs(["🔥 Monitoramento", "✨ Criar Edital"])

    with aba_ativas:
        formatar_titulo_aba("Monitoramento de Batalhas")
        formatar_legenda_instrucao("Acompanhe o desempenho das equipes em tempo real.")
        lista_ativas = listar_batalhas_ativas()
        if not lista_ativas:
            st.info("Nenhuma batalha ativa no momento.")
        else:
            for b in lista_ativas:
                with st.container(border=True):
                    st.markdown(f"**{b['titulo']}**")
                    if st.button("Encerrar Batalha", key=f"end_{b['id']}"): st.rerun()

    with aba_nova:
        formatar_titulo_aba("Publicar Edital")
        formatar_legenda_instrucao("Defina os parâmetros para uma nova rodada de batalha.")
        with st.form("form_nova_batalha"):
            titulo = st.text_input("Título")
            descricao = st.text_area("Descrição")
            if st.form_submit_button("Publicar"):
                cadastrar_nova_batalha(titulo, descricao, "")
                st.rerun()