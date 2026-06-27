import streamlit as st
import pandas as pd
from database.conexao import supabase

def calcular_ranking_quiz(quiz_id):
    try:
        res = supabase.table("respostas_quiz").select("pontuacao_obtida, usuarios(nome)").eq("quiz_id", quiz_id).execute()
        if not res.data:
            return pd.DataFrame(columns=["Nome", "Pontuação Total"])
        
        df = pd.DataFrame([{
            "Nome": r["usuarios"]["nome"] if r["usuarios"] else "Anônimo",
            "Pontuação Total": float(r["pontuacao_obtida"])
        } for r in res.data])
        
        ranking = df.groupby("Nome")["Pontuação Total"].sum().reset_index()
        return ranking.sort_values(by="Pontuação Total", ascending=False).reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=["Nome", "Pontuação Total"])

@st.fragment(run_every=3.0)
def renderizar_tabela_ranking(quiz_id):
    ranking_df = calcular_ranking_quiz(quiz_id)
    if ranking_df.empty:
        st.info("Nenhuma resposta computada para gerar o placar até o momento.")
    else:
        st.subheader("🎯 Classificação Atualizada")
        for idx, row in ranking_df.iterrows():
            medalha = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "👾"
            st.markdown(f"### {medalha} **{row['Nome']}** — `{int(row['Pontuação Total'])} pts`")

def tela_quiz_ranking_global():
    st.title("🏆 Telão de Líderes - Ranking Síncrono")
    quiz_id = st.session_state.get("quiz_ranking_id")
    if not quiz_id:
        st.warning("Nenhuma sala selecionada.")
        if st.button("⬅️ Voltar", key="btn_back_rank_missing"):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
        return

    renderizar_tabela_ranking(quiz_id)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Voltar ao Painel De Controle", use_container_width=True, key="btn_back_to_panel_main"):
        st.session_state.pagina = "quiz_ao_vivo"
        st.rerun()