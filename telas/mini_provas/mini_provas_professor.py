import streamlit as st
import datetime
from utils.estilo import aplicar_estilo, cabecalho
from services.mini_prova_service import (
    criar_escopo_mini_prova, 
    listar_provas_professor,
    salvar_questao_com_alternativas, 
    deletar_mini_prova
)

def tela_mini_provas_professor():
    aplicar_estilo()
    usuario_id = st.session_state.usuario_logado.get("id")
    cabecalho("Gestão de Mini-Provas", "Crie, edite e remova avaliações")

    # ABA DE CRIAÇÃO (ESCOPO)
    with st.expander("📝 Criar Nova Mini-Prova", expanded=True):
        with st.form("form_escopo", clear_on_submit=True):
            titulo = st.text_input("Título")
            disciplina = st.text_input("Disciplina")
            duracao = st.number_input("Duração (min)", value=30)
            xp = st.number_input("XP", value=100)
            instrucoes = st.text_area("Instruções")
            if st.form_submit_button("Salvar Prova"):
                res = criar_escopo_mini_prova(titulo, duracao, usuario_id, "2026-12-31", disciplina, xp, instrucoes)
                if res["sucesso"]: st.rerun()
                else: st.error(res["mensagem"])

    # LISTAGEM E DELEÇÃO
    st.subheader("🗑️ Provas Existentes")
    provas = listar_provas_professor(usuario_id)
    
    if not provas:
        st.info("Nenhuma prova criada.")
    else:
        for p in provas:
            col1, col2 = st.columns([5, 1])
            col1.write(f"**{p['titulo']}**")
            if col2.button("🗑️", key=f"del_{p['id']}"):
                res = deletar_mini_prova(p['id'])
                if res["sucesso"]: st.rerun()
                else: st.error("Erro ao deletar")

        # CADASTRO DE QUESTÕES (VINCLUADO À PROVA SELECIONADA)
        st.divider()
        prova_selecionada = st.selectbox("Vincular questões à:", [p['titulo'] for p in provas])
        prova_id = next(p['id'] for p in provas if p['titulo'] == prova_selecionada)

        with st.form("form_questao"):
            enunciado = st.text_area("Enunciado")
            a = st.text_input("A")
            b = st.text_input("B")
            c = st.text_input("C")
            d = st.text_input("D")
            correta = st.selectbox("Correta", ["A", "B", "C", "D"])
            if st.form_submit_button("Salvar Questão"):
                res = salvar_questao_com_alternativas(prova_id, enunciado, [a, b, c, d], correta)
                if res["sucesso"]: st.success("Salvo!")
                else: st.error(res["mensagem"])

    if st.button("⬅️ Voltar"):
        st.session_state.pagina = "mini_provas"
        st.rerun()