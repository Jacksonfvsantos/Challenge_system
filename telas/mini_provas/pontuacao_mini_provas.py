import streamlit as st
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

def tela_pontuacao_mini_provas():
    aplicar_estilo()
    
    usuario_logado = st.session_state.get("usuario_logado", {})
    usuario_id = usuario_logado.get("id")
    cabecalho("Minha Pontuação", "Veja seu desempenho nas mini-provas")

    if not usuario_id:
        st.error("Sessão expirada. Realize o login novamente.")
        return

    try:
        res_historico = (
            supabase.table("historico_provas")
            .select("usuario_id, nota, usuarios(nome, tipo_usuario)")
            .execute()
        )
        dados_historico = res_historico.data or []
    except Exception as e:
        st.error(f"Erro ao carregar ranking do banco de dados: {e}")
        return

    pontuacao_por_usuario = {}
    nomes_usuarios = {}

    for item in dados_historico:
        u_info = item.get("usuarios", {}) or {}
        if str(u_info.get("tipo_usuario", "aluno")).lower() == "professor":
            continue
            
        uid = item["usuario_id"]
        nota = float(item.get("nota", 0.0))
        nome = u_info.get("nome", "Usuário Anônimo")

        pontuacao_por_usuario[uid] = pontuacao_por_usuario.get(uid, 0.0) + nota
        nomes_usuarios[uid] = nome

    ranking_ordenado = sorted(pontuacao_por_usuario.items(), key=lambda x: x[1], reverse=True)
    pontos_proprios = pontuacao_por_usuario.get(usuario_id, 0.0)
    
    posicao_propria = 0
    for idx, (uid, _) in enumerate(ranking_ordenado):
        if uid == usuario_id:
            posicao_propria = idx + 1
            break
            
    if posicao_propria == 0:
        posicao_propria = len(ranking_ordenado) + 1

    col1, col2 = st.columns(2)
    col1.metric("Pontuação Total (Soma das Notas)", f"{pontos_proprios:.1f} pts")
    col2.metric("Posição no Ranking", f"{posicao_propria}º")

    st.divider()
    st.markdown("### Ranking Geral")

    if not ranking_ordenado:
        st.info("Nenhum registro de pontuação computado até o momento.")
    else:
        for idx, (uid, total_pontos) in enumerate(ranking_ordenado):
            posicao = idx + 1
            nome_competidor = nomes_usuarios[uid]
            
            if uid == usuario_id:
                st.markdown(
                    f"""
                    <div style="background:#f0f9ff; border-left:4px solid #ffb703; border-radius:6px; padding:10px 16px; margin-bottom:8px; display:flex; justify-content:between; align-items:center;">
                        <span style="color:#0d1b2a; font-weight:700;">{posicao}º — {nome_competidor} (Você)</span>
                        <span style="color:#ffb703; font-weight:700;">{total_pontos:.1f} pts</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="background:#f8f9fa; border-left:4px solid #ced4da; border-radius:6px; padding:10px 16px; margin-bottom:8px; display:flex; justify-content:between; align-items:center;">
                        <span style="color:#495057;">{posicao}º — {nome_competidor}</span>
                        <span style="color:#6c757d; font-weight:600;">{total_pontos:.1f} pts</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

    st.divider()
    if st.button("Voltar", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()