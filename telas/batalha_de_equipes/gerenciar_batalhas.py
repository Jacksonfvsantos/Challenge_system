import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho, formatar_titulo_aba, formatar_legenda_instrucao
from services.batalha_service import listar_batalhas_ativas, cadastrar_nova_batalha, listar_times

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
        formatar_titulo_aba("Abrir Novo Edital de Batalha")
        formatar_legenda_instrucao("Preencha os dados abaixo para publicar um novo desafio síncrono.")
        
        times = listar_times()
        
        with st.form("form_nova_batalha"):
            titulo = st.text_input("Título da Batalha")
            descricao = st.text_area("Descrição / Regras")
            
            # Novo seletor de times
            if not times:
                st.warning("Nenhum time cadastrado no sistema.")
                time_selecionado_id = None
            else:
                opcoes_times = {t["nome"]: t["id"] for t in times}
                nome_time_selecionado = st.selectbox("Selecione a Equipe Inicial:", list(opcoes_times.keys()))
                time_selecionado_id = opcoes_times[nome_time_selecionado]
            
            if st.form_submit_button("Publicar Edital"):
                if titulo and time_selecionado_id:
                    resultado = cadastrar_nova_batalha(titulo, descricao, time_selecionado_id)
                    if resultado.get("sucesso"):
                        st.success("Batalha criada com sucesso!")
                        st.rerun()
                    else:
                        st.error(resultado.get("mensagem", "Erro ao criar batalha."))
                else:
                    st.warning("O título e a equipe inicial são obrigatórios.")