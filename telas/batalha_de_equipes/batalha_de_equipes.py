import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import listar_batalhas_ativas, deletar_batalha

def tela_batalha_de_equipes():
    aplicar_estilo()
    
    if st.button("⬅️ Voltar ao Dashboard"):
        st.session_state.pagina = "home"
        st.rerun()
        
    cabecalho("⚔️ Arena de Batalha de Equipes", "Participe de rodadas síncronas e desafios de engenharia")

    todas_batalhas = listar_batalhas_ativas()
    
    aba_rebate, aba_assincrona = st.tabs(["⚡ Bate-Rebate (Síncrona)", "⏳ Batalha Assíncrona"])
    
    with aba_rebate:
        renderizar_lista_batalhas([b for b in todas_batalhas if b.get("modalidade") == "sincrona"])
    with aba_assincrona:
        renderizar_lista_batalhas([b for b in todas_batalhas if b.get("modalidade") == "assincrona"])

    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()

    if tipo_usuario in ("professor", "admin"):
        st.divider()
        st.markdown("### 🛠️ Painel Avançado de Governança Docente")
        col_m1, col_m2, col_m3 = st.columns(3)
        if col_m1.button("🏢 Gerenciar Equipes", use_container_width=True): st.session_state.pagina = "batalha_times"; st.rerun()
        if col_m2.button("👥 Alocação de Alunos", use_container_width=True): st.session_state.pagina = "batalha_integrantes"; st.rerun()
        if col_m3.button("📝 Abrir Nova Batalha", type="primary", use_container_width=True): st.session_state.pagina = "batalha_gerenciar"; st.rerun()
        if st.button("📜 Ver Histórico de Batalhas", use_container_width=True): st.session_state.pagina = "batalha_historico"; st.rerun()
        
        if st.button("🔄 Atualizar Lista de Arenas"):
            st.rerun()

def renderizar_lista_batalhas(lista):
    if not lista:
        st.info("Nenhuma batalha ativa nesta modalidade.")
        return
    
    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()

    for ba in lista:
        with st.container(border=True):
            col_titulo, col_del = st.columns([0.85, 0.15])
            with col_titulo:
                st.markdown(f"### {ba['titulo']}")
            with col_del:
                if tipo_usuario in ("professor", "admin"):
                    with st.popover("🗑️"):
                        st.warning("Tem certeza que deseja excluir esta arena?")
                        if st.button("Confirmar Exclusão", key=f"del_{ba['id']}"):
                            deletar_batalha(ba['id'])
                            st.rerun()
            
            st.write(ba.get("descricao", "Sem diretrizes anexadas."))
            
            if st.button(f"Entrar na Arena - {ba['titulo']}", key=f"entrar_{ba['id']}", use_container_width=True):
                st.session_state.batalha_ativa_id = ba["id"]
                st.session_state.pagina = "batalha_rodada"
                st.rerun()