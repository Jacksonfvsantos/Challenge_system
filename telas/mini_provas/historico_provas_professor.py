import streamlit as st
import time
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho

def tela_historico_provas_professor():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    
    cabecalho("📜 Histórico Geral de Provas Encerradas", "Gerencie o acervo de exames inativos e finalizados")

    if not usuario_id:
        st.error("Sessão inválida.")
        return

    try:
        res = (
            supabase.table("mini_provas")
            .select("id, titulo, descricao, quantidade_questoes, data_criacao")
            .eq("criado_por", usuario_id)
            .eq("status", "Indisponível")
            .order("data_criacao", desc=True)
            .execute()
        )
        provas_encerradas = res.data or []
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        provas_encerradas = []

    if not provas_encerradas:
        st.info("💡 Nenhuma mini-prova foi encerrada ou arquivada até o momento.")
        if st.button("⬅️ Voltar para o Painel Inicial", use_container_width=True):
            st.session_state.pagina = "mini_provas"
            st.rerun()
        return

    st.markdown(f"### 🗃️ Acervo de Avaliações Inativas ({len(provas_encerradas)})")
    st.caption("Atenção: Excluir uma prova apagará permanentemente suas questões, alternativas e notas vinculadas.")

    for prova in provas_encerradas:
        with st.container(border=True):
            col_txt, col_btn = st.columns([3, 1])
            
            with col_txt:
                st.markdown(f"""
                <strong style="color:#2b2d42; font-size:16px;">📋 {prova.get('titulo', 'Sem Título')}</strong><br>
                <span style="color:#6c757d; font-size:13px;">{prova.get('descricao', 'Sem descrição.')}</span><br>
                <span style="color:#e63946; font-size:12px; font-weight:600;">
                    ❌ Status: Encerrada de forma definitiva | 📝 {prova.get('quantidade_questoes', 0)} Questões
                </span>
                """, unsafe_allow_html=True)
            
            with col_btn:
                st.write("")
                with st.popover("🗑️ Deletar Prova", use_container_width=True):
                    st.warning("Tem certeza? Esta ação apagará permanentemente a prova, as questões e as notas!")
                    if st.button("Sim, Excluir do Banco", key=f"del_{prova['id']}", type="primary", use_container_width=True):
                        try:
                            res_questoes = supabase.table("questoes").select("id").eq("mini_prova_id", prova["id"]).execute()
                            lista_ids_questoes = [q["id"] for q in (res_questoes.data or [])]
                            
                            if lista_ids_questoes:
                                supabase.table("alternativas").delete().in_("questao_id", lista_ids_questoes).execute()
                                supabase.table("questoes").delete().eq("mini_prova_id", prova["id"]).execute()
                            
                            supabase.table("historico_provas").delete().eq("mini_prova_id", prova["id"]).execute()
                            supabase.table("mini_provas").delete().eq("id", prova["id"]).execute()
                            
                            st.success("Prova e todas as suas dependências removidas com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao deletar estrutura relacional: {e}")

    st.divider()
    if st.button("⬅️ Voltar para o Painel Geral", use_container_width=True, type="secondary"):
        st.session_state.pagina = "mini_provas"
        st.rerun()