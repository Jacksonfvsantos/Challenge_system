import streamlit as st
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

def tela_resultados_mini_provas():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    
    cabecalho("Meu Histórico", "Consulte as mini-provas já finalizadas e revise seus resultados")

    if not usuario_id:
        st.error("Sessão de usuário inválida.")
        return

    # 🔍 BUSCA O HISTÓRICO REFEITO COM OS CAMPOS REAIS DO SEU DDL (Apenas colunas existentes)
    try:
        res = supabase.table("historico_provas")\
            .select("*, mini_provas(titulo, descricao)")\
            .eq("usuario_id", usuario_id)\
            .order("created_at", desc=True)\
            .execute()
        historico = res.data or []
    except Exception as e:
        st.error(f"Erro ao carregar histórico do banco de dados: {e}")
        historico = []

    if not historico:
        st.info("💡 Você ainda não realizou nenhuma mini-prova neste semestre.")
        
        st.divider()
        if st.button("⬅️ Voltar para o Painel", use_container_width=True):
            st.session_state.pagina = "mini_provas"
            st.rerun()
        return

    st.caption(f"Você concluiu um total de {len(historico)} avaliação(ões).")
    st.markdown("<br>", unsafe_allow_html=True)

    # 📜 Listagem dinâmica das tentativas baseadas no esquema real do banco
    for idx, tentativa in enumerate(historico):
        prova_dados = tentativa.get("mini_provas", {}) or {}
        titulo_prova = prova_dados.get("titulo", "Mini Prova")
        descricao_prova = prova_dados.get("descricao", "Sem descrição.")
        
        nota = tentativa.get("nota", 0.0)
        pontos = tentativa.get("pontuacao", 0.0)  # ✅ Ajustado para a coluna 'pontuacao' do seu DDL
        acertos = tentativa.get("acertos", "0/0")  # ✅ Ajustado para a coluna 'acertos' (texto) do seu DDL
        
        # Define a cor do card com base no aproveitamento (Acima ou abaixo de 6.0)
        cor_borda = "#2a9d8f" if float(nota) >= 6.0 else "#e63946"

        with st.container(border=True):
            st.markdown(f"""
            <div style="border-left: 4px solid {cor_borda}; padding-left: 12px; margin-bottom: 8px;">
                <strong style="color: #1b3a5c; font-size: 16px;">{titulo_prova}</strong><br>
                <span style="color: #666; font-size: 13px;">📝 Detalhes: {descricao_prova}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Exibição das métricas da tentativa
            col1, col2, col3 = st.columns(3)
            col1.metric("🎯 Nota", f"{nota} / 10.0")
            col2.metric("⭐ Pontuação / XP", f"+{pontos} pts")
            col3.metric("📈 Taxa de Acertos", f"{acertos}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Botão reativo para abrir o Gabarito Detalhado
            if st.button(f"🔍 Ver Detalhes e Gabarito", key=f"ver_gabarito_{tentativa['id']}_{idx}", use_container_width=True):
                st.session_state.resultado_prova_calculado = {
                    "sucesso": True,
                    "nota": nota,
                    "pontos": pontos,
                    "acertos": acertos,
                    "mini_prova_id": tentativa.get("mini_prova_id"),
                    "historico_id": tentativa.get("id")
                }
                st.session_state.pagina = "resultado_mini_prova"
                st.rerun()

    st.divider()

    if st.button("⬅️ Voltar para o Painel Principal", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()