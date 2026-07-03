import streamlit as st
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import listar_batalhas_ativas, deletar_batalha

def tela_batalha_de_equipes():
    aplicar_estilo()
    
    if st.button("⬅️ Voltar ao Dashboard"):
        st.session_state.pagina = "home"
        st.rerun()
        
    cabecalho("⚔️ Arena de Batalha de Equipes", "Participe de desafios síncronos em tempo real")

    if st.button("🔄 Atualizar Lista de Arenas"):
        st.rerun()

    todas_batalhas = listar_batalhas_ativas()
    
    aba_sincrona, aba_assincrona = st.tabs(["⚡ Síncronas (Bate-Rebate)", "⏳ Assíncronas"])
    
    with aba_sincrona:
        renderizar_lista([b for b in todas_batalhas if b.get("modalidade") == "sincrona"])
    with aba_assincrona:
        renderizar_lista([b for b in todas_batalhas if b.get("modalidade") == "assincrona"])

def renderizar_lista(lista):
    if not lista:
        st.info("Nenhuma batalha ativa no momento.")
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
                    if st.button("🗑️", key=f"del_{ba['id']}"):
                        deletar_batalha(ba['id'])
                        st.rerun()

            st.write(ba.get("descricao", "Sem diretrizes."))

            if st.button(f"Entrar na Arena: {ba['titulo']}", key=f"entrar_{ba['id']}", use_container_width=True):
                st.session_state.batalha_ativa_id = ba["id"]
                st.session_state.pagina = "batalha_rodada"
                time.sleep(0.1)
                st.rerun()