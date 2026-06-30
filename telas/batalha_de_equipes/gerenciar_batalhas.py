import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho, formatar_titulo_aba, formatar_legenda_instrucao
from services.batalha_service import encerrar_partida_sincrona, iniciar_partida_sincrona, listar_batalhas_ativas, cadastrar_nova_batalha, listar_times

def tela_gerenciar_batalhas():
    aplicar_estilo()
    cabecalho("Gestão de Batalhas", "Administração de editais e monitoramento síncrono")

    aba_ativas, aba_nova = st.tabs(["🔥 Monitoramento", "✨ Criar Edital"])

    with aba_ativas:
        formatar_titulo_aba("Monitoramento de Batalhas")
    lista_ativas = listar_batalhas_ativas()

    if not lista_ativas:
        st.info("Nenhuma batalha encontrada. Verifique se o status no banco é 'agendada'.")
    else:
        for b in lista_ativas:
            with st.container(border=True):
                st.markdown(f"**{b['titulo']}** | Status: {b.get('status', 'N/A')}")
                
                if b.get('status') == 'agendada':
                    if st.button(f"Iniciar {b['titulo']}", key=f"start_{b['id']}"):
                        if iniciar_partida_sincrona(b['id'], b['time_a_id']):
                            st.rerun()
                
                elif b.get('status') == 'em_andamento':
                    if st.button("Encerrar Batalha", key=f"end_{b['id']}"):
                        encerrar_partida_sincrona(b['id'])
                        st.rerun()
    with aba_nova:
        formatar_titulo_aba("Abrir Novo Edital de Batalha")
        with st.form("form_nova_batalha"):
            titulo = st.text_input("Título da Batalha")
            descricao = st.text_area("Descrição / Regras")
            modalidade = st.selectbox("Modalidade:", ["sincrona", "assincrona"])
            
            times = listar_times()
            time_a = st.selectbox("Time A (Inicial):", options=[t['nome'] for t in times])
            time_b = st.selectbox("Time B (Adversário):", options=[t['nome'] for t in times])
        
            if st.form_submit_button("Publicar Edital"):
                t_a_id = next(t['id'] for t in times if t['nome'] == time_a)
                t_b_id = next(t['id'] for t in times if t['nome'] == time_b)
                
                res = cadastrar_nova_batalha(titulo, descricao, t_a_id, t_b_id, modalidade)
                if res["sucesso"]:
                    st.success("Batalha configurada!")
                    st.rerun()