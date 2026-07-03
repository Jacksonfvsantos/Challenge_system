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
        st.session_state.pagina = "home"
        st.rerun()
        
    cabecalho("⚔️ Arena de Batalha de Equipes", "Participe de desafios síncronos em tempo real")

    # --- GOVERNANÇA DOCENTE (Equipes e Questões) ---
    if tipo_usuario in ("professor", "admin"):
        with st.expander("👨‍🏫 Governança Docente"):
            # Sub-aba de Equipes
            with st.container():
                st.subheader("Gerenciar Equipes")
                for t in listar_times():
                    with st.expander(f"Time: {t['nome']}"):
                        if st.button("Excluir Time", key=f"del_time_{t['id']}"):
                            deletar_time(t['id']); st.rerun()
                        for m in listar_membros_time(t['id']):
                            col1, col2 = st.columns([0.8, 0.2])
                            col1.write(f"- {m['nome']}")
                            if col2.button("Remover", key=f"rem_{m['id']}_{t['id']}"):
                                remover_aluno(t['id'], m['id']); st.rerun()
            
            st.divider()
            
            # Sub-aba de Questões
            with st.container():
                st.subheader("📝 Cadastrar Questão na Arena")
                with st.form("form_cadastrar_questao"):
                    enunciado = st.text_area("Enunciado:")
                    a1 = st.text_input("Alt 1"); a2 = st.text_input("Alt 2")
                    a3 = st.text_input("Alt 3"); a4 = st.text_input("Alt 4")
                    correta = st.selectbox("Alternativa Correta:", [0, 1, 2, 3], format_func=lambda x: f"Alt {x+1}")
                    
                    if st.form_submit_button("Salvar Questão"):
                        # O professor seleciona a batalha ativa no contexto ou via seletor
                        b_sel = st.selectbox("Batalha destino:", listar_batalhas_ativas(), format_func=lambda x: x['titulo'])
                        res = cadastrar_questao_rapida(b_sel['id'], enunciado, [a1, a2, a3, a4], correta)
                        if res["sucesso"]: st.success("Questão salva!"); st.rerun()
                        else: st.error(res["mensagem"])

    # --- GESTÃO DE EQUIPES (ALUNOS) ---
    elif tipo_usuario == "aluno":
        if not aluno_tem_time(usuario_id):
            with st.expander("✨ Gerencie sua equipe:", expanded=True):
                col_c, col_e = st.columns(2)
                with col_c:
                    nome = st.text_input("Nome da Equipe:")
                    if st.button("🚀 Criar Equipe"): 
                        if criar_time(nome): st.rerun()
                with col_e:
                    times = listar_times()
                    if times:
                        sel = st.selectbox("Escolha:", times, format_func=lambda x: x['nome'])
                        if st.button("🤝 Entrar"): 
                            if entrar_no_time(sel['id'], usuario_id): st.rerun()
        else:
            st.success("✅ Você está alocado em um time.")

    # --- ARENA DE BATALHAS ---
    if st.button("🔄 Atualizar"): st.rerun()
    todas_batalhas = listar_batalhas_ativas()
    aba_s, aba_a = st.tabs(["⚡ Síncronas", "⏳ Assíncronas"])
    
    with aba_s, aba_a:
        lista = todas_batalhas if "sincrona" in st.tabs(["⚡ Síncronas", "⏳ Assíncronas"]) else [b for b in todas_batalhas if b.get("modalidade") == "sincrona"]
        renderizar_lista(lista)

def renderizar_lista(lista):
    for ba in lista:
        with st.container(border=True):
            col1, col2 = st.columns([0.8, 0.2])
            col1.markdown(f"### {ba['titulo']}")
            if st.button(f"Entrar: {ba['titulo']}", key=f"entrar_{ba['id']}", use_container_width=True):
                st.session_state.batalha_ativa_id = ba["id"]
                st.session_state.pagina = "batalha_rodada"
                st.rerun()