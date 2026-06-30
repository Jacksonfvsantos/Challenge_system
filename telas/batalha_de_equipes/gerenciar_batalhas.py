import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho, formatar_titulo_aba
from services.batalha_service import (
    listar_batalhas_ativas, deletar_batalha, iniciar_partida_sincrona, 
    encerrar_partida_sincrona, listar_times, cadastrar_nova_batalha
)

def tela_gerenciar_batalhas():
    aplicar_estilo()
  
    if st.button("⬅️ Voltar ao Painel"):
        st.session_state.pagina = "dashboard_professor" # Ajuste conforme necessário
        st.rerun()
    
    cabecalho("Gestão de Batalhas", "Administração de editais e monitoramento síncrono")

    aba_ativas, aba_nova = st.tabs(["🔥 Monitoramento", "✨ Criar Edital"])

    with aba_ativas:
        formatar_titulo_aba("Monitoramento de Batalhas")
        lista_ativas = listar_batalhas_ativas()

        if not lista_ativas:
            st.info("Nenhuma batalha encontrada.")
        else:
            for b in lista_ativas:
                with st.container(border=True):
                    st.markdown(f"**{b['titulo']}** | Status: {b.get('status', 'N/A')}")
                    col1, col2, col3 = st.columns(3)
                    
                    if b.get('status') == 'agendada':
                        if col1.button("▶️ Iniciar", key=f"start_{b['id']}"):
                            iniciar_partida_sincrona(b['id'], b.get('time_a_id'))
                            st.rerun()
                    elif b.get('status') == 'em_andamento':
                        if col2.button("⏹️ Encerrar", key=f"end_{b['id']}"):
                            encerrar_partida_sincrona(b['id'])
                            st.rerun()
                    
                    if col3.button("🗑️ Deletar", key=f"del_{b['id']}"):
                        deletar_batalha(b['id'])
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
                try:
                    t_a_id = next(t['id'] for t in times if t['nome'] == time_a)
                    t_b_id = next(t['id'] for t in times if t['nome'] == time_b)
    
                    res = cadastrar_nova_batalha(
                        titulo=titulo, 
                        descricao=descricao, 
                        time_a_id=t_a_id, 
                        time_b_id=t_b_id, 
                        modalidade=modalidade
                    )
                    
                    if res["sucesso"]:
                        st.success("Batalha configurada com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"Erro ao salvar: {res['mensagem']}")
                        
                except StopIteration:
                    st.error("Erro: Selecione times válidos cadastrados no sistema.")
                except Exception as e:
                    st.error(f"Erro inesperado: {str(e)}")