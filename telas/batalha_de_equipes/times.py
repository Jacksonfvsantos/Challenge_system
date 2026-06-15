import streamlit as st
from services.batalha_de_equipes_service import (
    listar_times, criar_time, editar_time, deletar_time,
    aluno_tem_time, entrar_no_time
)
from utils.estilo import aplicar_estilo, cabecalho


def tela_batalha_times():
    aplicar_estilo()

    usuario = st.session_state.usuario_logado
    tipo    = usuario.get("tipo_usuario", "aluno")
    user_id = str(usuario.get("id", "")).strip()  # Mantido permanentemente como string UUID

    cabecalho("Times", "Gerencie ou entre em um time")

    if st.button("⬅️ Voltar ao Painel de Batalhas"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    st.divider()

    # --------------------------------------------------
    # PROFESSOR
    # --------------------------------------------------
    if tipo == "professor":
        st.markdown("### ✨ Criar novo time")

        # Inicializa o estado para limpeza garantida do formulário (Item 5.97)
        if "input_nome_time" not in st.session_state:
            st.session_state["input_nome_time"] = ""

        with st.container(border=True):
            nome = st.text_input("Nome do time", value=st.session_state["input_nome_time"], placeholder="Ex: Time Alpha")
            
            if st.button("Gravar e Ativar Equipe", use_container_width=True):
                if not nome or not nome.strip():
                    st.warning("O nome do time não pode ser vazio.")
                else:
                    if criar_time(nome.strip()):
                        st.success(f"✅ Confirmação: O time '{nome.strip()}' foi registrado com sucesso!") # Item 5.96
                        st.session_state["input_nome_time"] = ""  # Limpa o campo (Item 5.97)
                        st.rerun()
                    else:
                        st.error("Erro interno ao registrar o time no servidor.")

        st.divider()
        st.markdown("### 📋 Times Cadastrados")

        times = listar_times()
        if not times:
            st.info("Nenhum time cadastrado ainda.")
            return

        for t in times:
            if not isinstance(t, dict): continue
            time_id    = str(t.get("id")).strip()
            nome_atual = t.get("nome", "")
            if not time_id or not nome_atual: continue

            with st.container(border=True):
                col_titulo, col_acoes = st.columns([3, 1])

                with col_titulo:
                    st.markdown(f"""
                    <div style="background:#f0f9ff; border-left:4px solid #00b4d8; border-radius:6px; padding:8px 12px;">
                        <strong style="color:#0d1b2a; font-size:16px;">{nome_atual}</strong>
                    </div>
                    """, unsafe_allow_html=True)

                with st.expander("📝 Editar / Deletar Equipe", expanded=False):
                    novo_nome = st.text_input("Alterar nome", value=nome_atual, key=f"edit_{time_id}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Salvar Alteração", key=f"salvar_{time_id}", use_container_width=True):
                            if not novo_nome.strip():
                                st.warning("Nome inválido.")
                            else:
                                editar_time(time_id, novo_nome.strip())
                                st.success("Atualizado com sucesso!")
                                st.rerun()
                    with col2:
                        if st.button("🗑️ Remover Equipe", key=f"deletar_{time_id}", use_container_width=True):
                            deletar_time(time_id)
                            st.success("Equipe excluída permanentemente.")
                            st.rerun()

    # --------------------------------------------------
    # ALUNO
    # --------------------------------------------------
    else:
        if not user_id:
            st.error("Sessão inválida.")
            return

        if aluno_tem_time(user_id):
            st.markdown("""
            <div style="background:#e0f7fa; border-left:4px solid #00b4d8; border-radius:8px; padding:16px 20px;">
                <strong style="color:#0d1b2a;">Você já está vinculado a um time.</strong><br>
                <span style="color:#555;">Acesse a aba 'Integrantes' no menu para interagir com sua equipe.</span>
            </div>
            """, unsafe_allow_html=True)
            return

        st.markdown("### 🚪 Entrar em um time")

        times = listar_times()
        if not times:
            st.info("Nenhum time disponível para ingresso no momento.")
            return

        mapa = {t.get("nome"): str(t.get("id")).strip() for t in times if isinstance(t, dict) and t.get("nome") and t.get("id")}

        if not mapa:
            st.error("Dados inválidos de times no servidor.")
            return

        sel = st.selectbox("Selecione a equipe desejada:", list(mapa.keys()))

        if st.button("Confirmar Ingresso", use_container_width=True):
            if entrar_no_time(mapa[sel], user_id):
                st.success(f"🎉 Sucesso! Você agora faz parte do time '{sel}'!")
                st.rerun()
            else:
                st.warning("Não foi possível concluir. Você já pertence a uma equipe.")