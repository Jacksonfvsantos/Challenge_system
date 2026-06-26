import streamlit as st
import pandas as pd
from database.conexao import supabase

def calcular_ranking_quiz(quiz_id):
    try:
        # Puxa os registros agregados de pontos
        res = supabase.table("respostas_quiz").select("pontuacao_obtida, usuarios(nome)").eq("quiz_id", quiz_id).execute()
        
        # ✅ CORRIGIDO: Se não houver dados, retorna um DataFrame vazio com as colunas estruturadas
        if not res.data:
            return pd.DataFrame(columns=["Nome", "Pontuação Total"])
        
        # Converte em DataFrame para agrupar e somar os pontos por aluno
        df = pd.DataFrame([{
            "Nome": r["usuarios"]["nome"] if r["usuarios"] else "Anônimo",
            "Pontuação Total": float(r["pontuacao_obtida"])
        } for r in res.data])
        
        ranking = df.groupby("Nome")["Pontuação Total"].sum().reset_index()
        return ranking.sort_values(by="Pontuação Total", ascending=False).reset_index(drop=True)
    except Exception:
        # ✅ CORRIGIDO: Retorna DataFrame vazio no bloco de exceção também
        return pd.DataFrame(columns=["Nome", "Pontuação Total"])

def tela_quiz_ranking_global():
    st.title("🏆 Telão de Líderes - Ranking Síncrono")
    
    quiz_id = st.session_state.get("quiz_ranking_id")
    if not quiz_id:
        st.warning("Nenhuma sala selecionada.")
        if st.button("⬅️ Voltar"):
            st.session_state.pagina = "quiz_ao_vivo"
            st.rerun()
        return

    # Auto-refresh permanente para atualizar o placar conforme os alunos respondem
    st.iframe(
        src="data:text/html;charset=utf-8," + """
        <script>
            if (!window.refreshIntervalSet) {
                window.refreshIntervalSet = true;
                setInterval(function() { window.parent.postMessage({type: 'streamlit:setComponentValue', value: true}, '*'); }, 3000);
            }
        </script>
        """,
        height=1
    )

    ranking_df = calcular_ranking_quiz(quiz_id)

    # ✅ Agora funciona perfeitamente pois ranking_df sempre será um DataFrame
    if ranking_df.empty:
        st.info("Nenhuma resposta computada para gerar o placar até o momento.")
    else:
        st.subheader("🎯 Classificação Atualizada")
        
        # Estilização do Top 3
        for idx, row in ranking_df.iterrows():
            medalha = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "👾"
            st.markdown(f"### {medalha} **{row['Nome']}** — `{int(row['Pontuação Total'])} pts`")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Voltar ao Painel de Controle", use_container_width=True):
        st.session_state.pagina = "quiz_ao_vivo"
        st.rerun()