import streamlit as st
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import (
    listar_batalhas_ativas, 
    deletar_batalha,
    criar_time,
    listar_times,
    entrar_no_time,
    aluno_tem_time    
)

def tela_batalha_de_equipes():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    if st.button("⬅️ Voltar ao Dashboard"):
        st.session_state.pagina = "home"
        st.rerun()
        
    cabecalho("⚔️ Arena de Batalha de Equipes", "Participe de desafios síncronos em tempo real")

    if tipo_usuario == "aluno":
        if not aluno_tem_time(usuario_id):
            with st.expander("✨ Você ainda não tem um time! Gerencie aqui:", expanded=True):
                col_criar, col_entrar = st.columns(2)
                
                with col_criar:
                    nome_novo = st.text_input("Nome da Equipa:")
                    if st.button("🚀 Criar Equipa"):
                        if criar_time(nome_novo):
                            st.success("Equipa criada!")
                            st.rerun()
                
                with col_entrar:
                    times = listar_times()
                    if times:
                        time_sel = st.selectbox("Escolha uma equipa:", options=times, format_func=lambda x: x['nome'])
                        if st.button("🤝 Entrar na Equipe"):
                            if entrar_no_time(time_sel['id'], usuario_id):
                                st.success("Vinculado com sucesso!")
                                st.rerun()
                    else:
                        st.info("Nenhuma equipa disponível.")
        else:
            st.success("✅ Você já está alocado em uma equipe e pronto para a arena.")
    else:
        st.info("👤 Painel Docente: Gerenciamento de times oculto para alunos.")

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