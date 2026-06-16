import streamlit as st
import pandas as pd
from database.conexao import supabase
from services.batalha_de_equipes_service import (
    listar_times, listar_membros_time, listar_alunos,
    adicionar_aluno, remover_aluno, mover_aluno
)
from utils.estilo import aplicar_estilo, cabecalho


def _safe_dict(v): return v if isinstance(v, dict) else {}
def _safe_list(v): return v if isinstance(v, list) else []


def tela_batalha_integrantes():
    aplicar_estilo()

    usuario = st.session_state.usuario_logado
    tipo    = usuario.get("tipo_usuario", "aluno")
    user_id = str(usuario.get("id", "")).strip()

    cabecalho("Integrantes dos Times", "Veja e gerencie os membros de cada equipe")

    if st.button("⬅️ Voltar ao Painel"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    st.divider()

    times = listar_times()
    if not times:
        st.warning("Nenhum time cadastrado no sistema.")
        return
        
    mapa_times = {t.get("nome"): str(t.get("id")).strip() for t in times if isinstance(t, dict) and t.get("nome") and t.get("id")}

    st.markdown("### 🔍 Filtrar Visualização")
    time_selecionado_nome = st.selectbox("Selecione a equipe para listar os integrantes:", list(mapa_times.keys()), key="filtro_equipe_global")
    time_id_ativo = mapa_times[time_selecionado_nome]

    if tipo != "professor":
        st.markdown(f"📍 Exibindo dados para a equipe: **{time_selecionado_nome}**")

    st.markdown("### 👥 Quadro de Membros")
    membros = listar_membros_time(time_id_ativo)

    if not membros:
        st.info("Nenhum integrante associado a esta equipe até o momento.")
    else:
        dados_tabela = []
        for m in membros:
            dados_tabela.append({
                "Nome do Integrante": m.get("nome", "Não informado"),
                "E-mail de Contato": m.get("email", "-"),
                "Equipe Atual": time_selecionado_nome
            })
        
        df_membros = pd.DataFrame(dados_tabela)
        st.dataframe(df_membros, use_container_width=True, hide_index=True)

    if tipo != "professor":
        return

    st.divider()
    st.markdown("### 🛠️ Ações de Gestão de Membros")
    
    with st.expander("➕ Adicionar Novo Integrante (Janela de Cadastro)", expanded=False):
        alunos = listar_alunos()
        mapa_add = {a.get("nome"): str(a.get("id")).strip() for a in alunos if isinstance(a, dict) and a.get("nome") and a.get("id")}
        
        if mapa_add:
            sel_add = st.selectbox("Selecione o Aluno para Inclusão:", list(mapa_add.keys()), key="modal_add_aluno")
            if st.button("Confirmar Vínculo na Equipe", use_container_width=True):
                if adicionar_aluno(time_id_ativo, mapa_add[sel_add]):
                    st.success("✅ Aluno matriculado e vinculado à equipe com sucesso!")
                    st.rerun()
                else:
                    st.warning("Aviso: Este aluno já possui vínculo ativo com outra equipe.")
        else:
            st.info("Nenhum estudante disponível para alocação.")

    if membros:
        mapa_membros_ativos = {m.get("nome"): str(m.get("id")).strip() for m in membros if isinstance(m, dict) and m.get("nome") and m.get("id")}
        
        col_rem, col_trans = st.columns(2)
        
        with col_rem:
            with st.container(border=True):
                st.markdown("❌ **Remover Integrante**")
                sel_rm = st.selectbox("Escolha quem deseja remover:", list(mapa_membros_ativos.keys()), key="sb_remover_membro")
                if st.button("Confirmar Desvinculação", type="primary", use_container_width=True):
                    remover_aluno(time_id_ativo, mapa_membros_ativos[sel_rm])
                    st.success("Membro removido da equipe com sucesso.")
                    st.rerun()
                    
        with col_trans:
            with st.container(border=True):
                st.markdown("🔄 **Transferir entre Equipes**")
                sel_mv = st.selectbox("Escolha quem deseja mover:", list(mapa_membros_ativos.keys()), key="sb_mover_membro")
                destino_nome = st.selectbox("Selecione a equipe de destino:", [name for name in mapa_times.keys() if name != time_selecionado_nome], key="sb_destino_membro")
                
                if st.button("Executar Transferência", use_container_width=True):
                    mover_aluno(mapa_membros_ativos[sel_mv], mapa_times[destino_nome])
                    st.success(f"✅ Sucesso! Integrante transferido para o time '{destino_nome}'.")
                    st.rerun()