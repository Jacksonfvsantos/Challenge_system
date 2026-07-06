import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho
from services.recompensa_service import (
    criar_recompensa, 
    listar_recompensas, 
    editar_recompensa, 
    deletar_recompensa,
    solicitar_resgate,
    listar_solicitacoes_pendentes,
    alterar_status_solicitacao
)

def tela_recompensas():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho(
        "🏆 Vitrine de Recompensas",
        "Acompanhe suas insígnias, troque seus pontos e gerencie seus benefícios."
    )

    if tipo_usuario in ("professor", "admin"):
        aba_pedidos, aba_cadastro = st.tabs(["📥 Pedidos de Resgate", "✨ Cadastrar Nova Recompensa"])
        with aba_cadastro:
            with st.container(border=True):
                col_t1, col_t2 = st.columns([2, 1])
                with col_t1:
                    titulo = st.text_input("Título da Recompensa:", placeholder="Ex: Mestre do Refactoring")
                with col_t2:
                    tipo = st.selectbox("Categoria:", ["medalha", "vantagem", "bonus"])
                descricao = st.text_area("Diretrizes / Descrição da Conquista:", placeholder="Ex: Concedido ao aluno que otimizar o algoritmo...")
                custo = st.number_input("Custo ou Pontuação Bônus (XP):", min_value=0, value=10, step=5)
                
                if st.button("Gravar e Publicar Recompensa", type="primary", use_container_width=True):
                    if not titulo.strip():
                        st.error("O título da recompensa é obrigatório.")
                    elif criar_recompensa(titulo, descricao, custo, tipo, usuario_id):
                        st.success(f"🎉 Recompensa '{titulo}' publicada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro operacional ao salvar no servidor.")

        with aba_pedidos:
            st.markdown("#### Solicitações Aguardando sua Permissão")
            pedidos = listar_solicitacoes_pendentes()
            if not pedidos:
                st.info("Nenhum pedido de resgate pendente no momento.")
            else:
                for p in pedidos:
                    p_id = p["id"]
                    aluno_nome = p.get("usuarios", {}).get("nome", "Estudante")
                    recompensa_titulo = p.get("recompensas", {}).get("titulo", "Item")
                    custo_xp = p.get("recompensas", {}).get("custo_pontos", 0)
                    
                    with st.container(border=True):
                        col_p_info, col_p_ok, col_p_no = st.columns([3, 1, 1])
                        with col_p_info:
                            st.markdown(f"👤 **{aluno_nome}** solicitou **{recompensa_titulo}**")
                            st.caption(f"Valor a ser computado/debitado: **{custo_xp} XP**")
                        with col_p_ok:
                            if st.button("👍 Permitir", key=f"ok_{p_id}", use_container_width=True):
                                if alterar_status_solicitacao(p_id, "autorizado"):
                                    st.toast(f"Resgate de {aluno_nome} autorizado!", icon="✅")
                                    st.rerun()
                        with col_p_no:
                            if st.button("👎 Recusar", key=f"no_{p_id}", type="primary", use_container_width=True):
                                if alterar_status_solicitacao(p_id, "recusado"):
                                    st.toast(f"Pedido de {aluno_nome} recusado.", icon="❌")
                                    st.rerun()
        st.divider()

    st.markdown("### 📋 Vitrine de Conquistas Disponíveis")
    recompensas = listar_recompensas()
    if not recompensas:
        st.info("Nenhuma recompensa ou insígnia foi localizada na vitrine.")
        return

    for r in recompensas:
        r_id = str(r["id"]).strip()
        badge_emoji = "🥇" if r["tipo"] == "medalha" else "⚡" if r["tipo"] == "vantagem" else "🎁"
        with st.container(border=True):
            col_info, col_acao = st.columns([3, 1])
            with col_info:
                st.markdown(f"### {badge_emoji} {r['titulo']} <span style='font-size:12px; background:#e2e8f0; color:#4a5568; padding:2px 8px; border-radius:10px;'>{r['tipo'].upper()}</span>", unsafe_allow_html=True)
                st.write(r["descricao"])
                st.markdown(f"**Requisito/Custo:** `{r['custo_pontos']} XP`")
            with col_acao:
                st.markdown("<br>", unsafe_allow_html=True)
                if tipo_usuario == "aluno":
                    if st.button("🛒 Resgatar", key=f"claim_{r_id}", type="primary", use_container_width=True):
                        retorno = solicitar_resgate(r_id, usuario_id)
                        if retorno["sucesso"]:
                            st.success(retorno["mensagem"])
                        else:
                            st.warning(retorno["mensagem"])
                else:
                    col_e, col_d = st.columns(2)
                    with col_e:
                        with st.popover("📝", use_container_width=True):
                            st.markdown("**Editar Item**")
                            edit_titulo = st.text_input("Título:", value=r["titulo"], key=f"t_{r_id}")
                            edit_tipo = st.selectbox("Categoria:", ["medalha", "vantagem", "bonus"], index=["medalha", "vantagem", "bonus"].index(r["tipo"]), key=f"tp_{r_id}")
                            edit_desc = st.text_area("Descrição:", value=r["descricao"], key=f"d_{r_id}")
                            edit_custo = st.number_input("Pontos:", min_value=0, value=int(r["custo_pontos"]), key=f"c_{r_id}")
                            if st.button("Salvar", key=f"save_{r_id}", use_container_width=True):
                                if edit_titulo.strip() and editar_recompensa(r_id, edit_titulo, edit_desc, edit_custo, edit_tipo):
                                    st.success("Item atualizado!")
                                    st.rerun()
                    with col_d:
                        if st.button("🗑️", key=f"del_{r_id}", type="primary", use_container_width=True):
                            if deletar_recompensa(r_id):
                                st.success("Removido!")
                                st.rerun()