import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho, renderizar_card
from services.mini_prova_service import listar_mini_provas

def tela_mini_provas():
    aplicar_estilo()
    cabecalho("Mini-provas", "Realize as provas disponíveis")

    provas = listar_mini_provas()
    
    if not provas:
        st.info("Nenhuma mini-prova disponível no momento.")
    
    for prova in provas:
        footer_text = f"📝 {prova.get('quantidade_questoes', '-')} Questões | ⏱️ {prova.get('duracao_minutos', '-')} min"
        
        renderizar_card(
            titulo=prova.get('titulo', 'Sem Título'),
            descricao=prova.get('descricao', 'Sem descrição definida.'),
            cor_borda="#00b4d8",
            footer=footer_text
        )
        
        if st.button(f"Iniciar {prova.get('titulo')}", key=f"btn_prova_{prova.get('id')}", use_container_width=True):
            st.session_state.prova_ativa_id = prova.get('id')
            st.session_state.pagina = "realizar_mini_prova"
            st.rerun()