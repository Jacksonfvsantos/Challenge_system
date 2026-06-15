import streamlit as st
<<<<<<< HEAD
import pandas as pd
=======
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
from database.conexao import supabase
from services.batalha_de_equipes_service import (
    listar_times, listar_membros_time, listar_alunos,
    adicionar_aluno, remover_aluno, mover_aluno
)
from utils.estilo import aplicar_estilo, cabecalho


<<<<<<< HEAD
def _safe_dict(v): return v if isinstance(v, dict) else {}
def _safe_list(v): return v if isinstance(v, list) else []


def tela_batalha_integrantes():
=======
def _safe_dict(v):
    return v if isinstance(v, dict) else {}


def _safe_list(v):
    return v if isinstance(v, list) else []


def tela_batalha_integrantes():

>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
    aplicar_estilo()

    usuario = st.session_state.usuario_logado
    tipo    = usuario.get("tipo_usuario", "aluno")
<<<<<<< HEAD
    user_id = str(usuario.get("id", "")).strip()  # Tratado como string UUID para evitar quebras

    cabecalho("Integrantes dos Times", "Veja e gerencie os membros de cada equipe")

    if st.button("⬅️ Voltar ao Painel"):
=======
    user_id = usuario.get("id")

    cabecalho("Integrantes dos Times", "Veja e gerencie os membros de cada time")

    if st.button("Voltar"):
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    st.divider()

<<<<<<< HEAD
    # Captura de todos os times para alimentar os filtros solicitados
    times = listar_times()
    if not times:
        st.warning("Nenhum time cadastrado no sistema.")
        return
        
    mapa_times = {t.get("nome"): str(t.get("id")).strip() for t in times if isinstance(t, dict) and t.get("nome") and t.get("id")}

    # --- FILTRO POR EQUIPE EXIGIDO NO RELATÓRIO (Item 5.105) ---
    st.markdown("### 🔍 Filtrar Visualização")
    time_selecionado_nome = st.selectbox("Selecione a equipe para listar os integrantes:", list(mapa_times.keys()), key="filtro_equipe_global")
    time_id_ativo = mapa_times[time_selecionado_nome]

    # Ajuste do painel visual do aluno se ele não for o professor da listagem
    if tipo != "professor":
        st.markdown(f"📍 Exibindo dados para a equipe: **{time_selecionado_nome}**")

    # --- TABELA DE INTEGRANTES ESTRUTURADA (Item 5.104) ---
    st.markdown("### 👥 Quadro de Membros")
    membros = listar_membros_time(time_id_ativo)

    if not membros:
        st.info("Nenhum integrante associado a esta equipe até o momento.")
    else:
        # Monta um DataFrame estruturado de forma legível
        dados_tabela = []
        for m in membros:
            dados_tabela.append({
                "Nome do Integrante": m.get("nome", "Não informado"),
                "E-mail de Contato": m.get("email", "-"),
                "Equipe Atual": time_selecionado_nome
            })
        
        df_membros = pd.DataFrame(dados_tabela)
        st.dataframe(df_membros, use_container_width=True, hide_index=True)
=======
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        st.error("Sessao invalida.")
        return

    if tipo == "professor":
        times = listar_times()
        if not times:
            st.warning("Nenhum time cadastrado.")
            return
        mapa = {
            t.get("nome"): t.get("id")
            for t in times
            if isinstance(t, dict) and t.get("nome") and t.get("id")
        }
        if not mapa:
            st.warning("Times com dados invalidos.")
            return
        sel     = st.selectbox("Selecione o time", list(mapa.keys()))
        time_id = mapa[sel]

    else:
        res  = supabase.table("time_membros") \
            .select("time_id, times(id,nome)") \
            .eq("usuario_id", user_id) \
            .execute()
        data = _safe_list(getattr(res, "data", None))

        if not data:
            st.markdown("""
            <div style="
                background:#fff3e0;
                border-left:4px solid #0d1b2a;
                border-radius:8px;
                padding:14px 18px;
            ">
                <strong style="color:#0d1b2a;">Voce nao participa de nenhum time ainda.</strong>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Entrar em um time"):
                st.session_state.pagina = "batalha_times"
                st.rerun()
            return

        first_row = _safe_dict(data[0])
        time_info = first_row.get("times")
        if isinstance(time_info, list):
            time_info = time_info[0] if time_info else {}
        time_info = _safe_dict(time_info)

        if not time_info.get("id") or not time_info.get("nome"):
            st.error("Erro ao carregar time.")
            return

        time_id = time_info["id"]
        st.markdown(f"""
        <div style="
            background:#e0f7fa;
            border-left:4px solid #00b4d8;
            border-radius:8px;
            padding:12px 16px;
            margin-bottom:12px;
        ">
            <strong style="color:#0d1b2a;">Seu time: {time_info['nome']}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Membros")

    membros = listar_membros_time(time_id)

    if not membros:
        st.info("Nenhum membro neste time.")
    else:
        st.dataframe(
            membros,
            column_config={
                "id":    st.column_config.NumberColumn("ID"),
                "nome":  st.column_config.TextColumn("Nome"),
                "email": st.column_config.TextColumn("E-mail"),
            },
            use_container_width=True,
            hide_index=True
        )
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e

    if tipo != "professor":
        return

<<<<<<< HEAD
    # --- JANELA MODAL/POPUP DE INCLUSÃO SIMULADA POR BOTÃO '+' (Item 5.107) ---
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

    # --- OPERAÇÕES DE REMOÇÃO E TRANSFERÊNCIA EXIGIDAS (Item 5.106) ---
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
=======
    st.divider()
    st.markdown("### Gestao de membros")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("**Adicionar aluno**")
            alunos   = listar_alunos()
            mapa_add = {
                a.get("nome"): a.get("id")
                for a in alunos
                if isinstance(a, dict) and a.get("nome") and a.get("id")
            }
            if mapa_add:
                sel_add = st.selectbox("Aluno", list(mapa_add.keys()), key="add_aluno")
                if st.button("Adicionar", use_container_width=True):
                    if adicionar_aluno(time_id, mapa_add[sel_add]):
                        st.success("Aluno adicionado!")
                    else:
                        st.warning("Este aluno ja pertence a um time.")
                    st.rerun()
            else:
                st.info("Nenhum aluno disponivel.")

    with col2:
        with st.container(border=True):
            st.markdown("**Remover membro**")
            mapa_rm = {
                m.get("nome"): m.get("id")
                for m in membros
                if isinstance(m, dict) and m.get("nome") and m.get("id")
            }
            if mapa_rm:
                sel_rm = st.selectbox("Membro", list(mapa_rm.keys()), key="rm_aluno")
                if st.button("Remover", use_container_width=True):
                    remover_aluno(time_id, mapa_rm[sel_rm])
                    st.success("Membro removido.")
                    st.rerun()
            else:
                st.info("Nenhum membro para remover.")

    st.divider()

    with st.expander("Mover aluno para outro time", expanded=False):
        todos_times = listar_times()
        mapa_times  = {
            t.get("nome"): t.get("id")
            for t in todos_times
            if isinstance(t, dict) and t.get("nome") and t.get("id")
        }
        mapa_mv = {
            m.get("nome"): m.get("id")
            for m in membros
            if isinstance(m, dict) and m.get("nome") and m.get("id")
        }
        if mapa_mv and mapa_times:
            col3, col4 = st.columns(2)
            with col3:
                aluno_mv = st.selectbox("Aluno", list(mapa_mv.keys()), key="mover_aluno")
            with col4:
                destino  = st.selectbox("Destino", list(mapa_times.keys()), key="mover_destino")
            if st.button("Mover", use_container_width=True):
                mover_aluno(mapa_mv[aluno_mv], mapa_times[destino])
                st.success("Aluno movido!")
                st.rerun()
        else:
            st.info("Sem dados suficientes para mover alunos.")
import streamlit as st
from database.conexao import supabase
from services.batalha_de_equipes_service import (
    listar_times, listar_membros_time, listar_alunos,
    adicionar_aluno, remover_aluno, mover_aluno
)
from utils.estilo import aplicar_estilo, cabecalho


def _safe_dict(v):
    return v if isinstance(v, dict) else {}


def _safe_list(v):
    return v if isinstance(v, list) else []


def tela_batalha_integrantes():

    aplicar_estilo()

    usuario = st.session_state.usuario_logado
    tipo    = usuario.get("tipo_usuario", "aluno")
    user_id = usuario.get("id")

    cabecalho("Integrantes dos Times", "Veja e gerencie os membros de cada time")

    if st.button("Voltar"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    st.divider()

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        st.error("Sessao invalida.")
        return

    if tipo == "professor":
        times = listar_times()
        if not times:
            st.warning("Nenhum time cadastrado.")
            return
        mapa = {
            t.get("nome"): t.get("id")
            for t in times
            if isinstance(t, dict) and t.get("nome") and t.get("id")
        }
        if not mapa:
            st.warning("Times com dados invalidos.")
            return
        sel     = st.selectbox("Selecione o time", list(mapa.keys()))
        time_id = mapa[sel]

    else:
        res  = supabase.table("time_membros") \
            .select("time_id, times(id,nome)") \
            .eq("usuario_id", user_id) \
            .execute()
        data = _safe_list(getattr(res, "data", None))

        if not data:
            st.markdown("""
            <div style="
                background:#fff3e0;
                border-left:4px solid #0d1b2a;
                border-radius:8px;
                padding:14px 18px;
            ">
                <strong style="color:#0d1b2a;">Voce nao participa de nenhum time ainda.</strong>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Entrar em um time"):
                st.session_state.pagina = "batalha_times"
                st.rerun()
            return

        first_row = _safe_dict(data[0])
        time_info = first_row.get("times")
        if isinstance(time_info, list):
            time_info = time_info[0] if time_info else {}
        time_info = _safe_dict(time_info)

        if not time_info.get("id") or not time_info.get("nome"):
            st.error("Erro ao carregar time.")
            return

        time_id = time_info["id"]
        st.markdown(f"""
        <div style="
            background:#e0f7fa;
            border-left:4px solid #00b4d8;
            border-radius:8px;
            padding:12px 16px;
            margin-bottom:12px;
        ">
            <strong style="color:#0d1b2a;">Seu time: {time_info['nome']}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Membros")

    membros = listar_membros_time(time_id)

    if not membros:
        st.info("Nenhum membro neste time.")
    else:
        st.dataframe(
            membros,
            column_config={
                "id":    st.column_config.NumberColumn("ID"),
                "nome":  st.column_config.TextColumn("Nome"),
                "email": st.column_config.TextColumn("E-mail"),
            },
            use_container_width=True,
            hide_index=True
        )

    if tipo != "professor":
        return

    st.divider()
    st.markdown("### Gestao de membros")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("**Adicionar aluno**")
            alunos   = listar_alunos()
            mapa_add = {
                a.get("nome"): a.get("id")
                for a in alunos
                if isinstance(a, dict) and a.get("nome") and a.get("id")
            }
            if mapa_add:
                sel_add = st.selectbox("Aluno", list(mapa_add.keys()), key="add_aluno")
                if st.button("Adicionar", use_container_width=True):
                    if adicionar_aluno(time_id, mapa_add[sel_add]):
                        st.success("Aluno adicionado!")
                    else:
                        st.warning("Este aluno ja pertence a um time.")
                    st.rerun()
            else:
                st.info("Nenhum aluno disponivel.")

    with col2:
        with st.container(border=True):
            st.markdown("**Remover membro**")
            mapa_rm = {
                m.get("nome"): m.get("id")
                for m in membros
                if isinstance(m, dict) and m.get("nome") and m.get("id")
            }
            if mapa_rm:
                sel_rm = st.selectbox("Membro", list(mapa_rm.keys()), key="rm_aluno")
                if st.button("Remover", use_container_width=True):
                    remover_aluno(time_id, mapa_rm[sel_rm])
                    st.success("Membro removido.")
                    st.rerun()
            else:
                st.info("Nenhum membro para remover.")

    st.divider()

    with st.expander("Mover aluno para outro time", expanded=False):
        todos_times = listar_times()
        mapa_times  = {
            t.get("nome"): t.get("id")
            for t in todos_times
            if isinstance(t, dict) and t.get("nome") and t.get("id")
        }
        mapa_mv = {
            m.get("nome"): m.get("id")
            for m in membros
            if isinstance(m, dict) and m.get("nome") and m.get("id")
        }
        if mapa_mv and mapa_times:
            col3, col4 = st.columns(2)
            with col3:
                aluno_mv = st.selectbox("Aluno", list(mapa_mv.keys()), key="mover_aluno")
            with col4:
                destino  = st.selectbox("Destino", list(mapa_times.keys()), key="mover_destino")
            if st.button("Mover", use_container_width=True):
                mover_aluno(mapa_mv[aluno_mv], mapa_times[destino])
                st.success("Aluno movido!")
                st.rerun()
        else:
            st.info("Sem dados suficientes para mover alunos.")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
