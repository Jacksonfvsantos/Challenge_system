import streamlit as st
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import (
    listar_batalhas_ativas, deletar_batalha, criar_time, listar_times,
    entrar_no_time, aluno_tem_time, listar_membros_time,
    remover_aluno, deletar_time, cadastrar_questao_rapida
)

def tela_batalha_de_equipes():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario") or usuario.get("tipo") or "aluno").lower()

    if st.button("⬅️ Voltar ao Dashboard"):
        st.session_state.pagina = "home"; st.rerun()
        
    cabecalho("⚔️ Arena de Batalha de Equipes", "Participe de desafios síncronos em tempo real")

    # --- GOVERNANÇA DOCENTE ---
    if tipo_usuario in ("professor", "admin"):
        with st.expander("👨‍🏫 Governança Docente"):
            st.subheader("Gerenciar Equipes")
            for t in listar_times():
                with st.expander(f"Time: {t['nome']}"):
                    if st.button("Excluir Time", key=f"del_time_{t['id']}"):
                        deletar_time(t['id']); st.rerun()
                    for m in listar_membros_time(t['id']):
                        c1, c2 = st.columns([0.8, 0.2])
                        c1.write(f"- {m['nome']}")
                        if c2.button("Remover", key=f"rem_{m['id']}_{t['id']}"):
                            remover_aluno(t['id'], m['id']); st.rerun()
            
            st.divider()
            st.subheader("📝 Cadastrar Questão")
            modo = st.radio("Método:", ["Manual", "Via IA"], horizontal=True)

            if modo == "Manual":
                with st.form("form_manual"):
                    enun = st.text_area("Enunciado:")
                    a1, a2 = st.text_input("Alt A"), st.text_input("Alt B")
                    a3, a4 = st.text_input("Alt C"), st.text_input("Alt D")
                    correta = st.selectbox("Correta:", [0, 1, 2, 3])
                    b_sel = st.selectbox("Batalha:", listar_batalhas_ativas(), format_func=lambda x: x['titulo'])
                    
                    if st.form_submit_button("Salvar Questão"):
                        res = cadastrar_questao_rapida(b_sel['id'], enun, [a1, a2, a3, a4], correta)
                        if res["sucesso"]: st.success("Salvo!"); st.rerun()
                        else: st.error(res["mensagem"])
            else:
                texto_base = st.text_area("Conteúdo base para IA:")
                if st.button("Gerar com IA"):
                    st.info("Funcionalidade de IA em implementação...")

    # --- GESTÃO DE EQUIPES (ALUNOS) ---
    elif tipo_usuario == "aluno":
        if not aluno_tem_time(usuario_id):
            with st.expander("✨ Gerencie sua equipe:", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🚀 Criar Equipe"): criar_time(st.text_input("Nome:"))
                with c2:
                    times = listar_times()
                    if times and st.button("🤝 Entrar"): entrar_no_time(st.selectbox("Escolha:", times, format_func=lambda x: x['nome'])['id'], usuario_id)
        else: st.success("✅ Você está em um time.")

    # --- ARENA DE BATALHAS ---
    todas = listar_batalhas_ativas()
    sinc, assinc = st.tabs(["⚡ Síncronas", "⏳ Assíncronas"])
    
    with sinc: renderizar_lista([b for b in todas if b.get("modalidade") == "sincrona"])
    with assinc: renderizar_lista([b for b in todas if b.get("modalidade") == "assincrona"])

def renderizar_lista(lista):
    if not lista: st.info("Nenhuma batalha aqui."); return
    for ba in lista:
        with st.container(border=True):
            if st.button(f"Entrar: {ba['titulo']}", key=f"entrar_{ba['id']}", use_container_width=True):
                st.session_state.batalha_ativa_id = ba["id"]; st.session_state.pagina = "batalha_rodada"; st.rerun()