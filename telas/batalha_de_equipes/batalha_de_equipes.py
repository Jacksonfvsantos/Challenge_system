import streamlit as st
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia
from services.batalha_service import (
    listar_batalhas_ativas, deletar_batalha, criar_time, listar_times,
    entrar_no_time, aluno_tem_time, listar_membros_time,
    remover_aluno, deletar_time, cadastrar_questao_rapida, salvar_questoes_lote_ia
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
            st.subheader("⚙️ Nova Arena")
        with st.form("form_batalha"):
            titulo_b = st.text_input("Título da Arena:")
            modalidade = st.selectbox("Modalidade:", ["sincrona", "assincrona"])
            if st.form_submit_button("Criar Arena"):
                from services.batalha_service import cadastrar_nova_batalha
                cadastrar_nova_batalha(titulo_b, "Arena criada pelo professor", None, None, modalidade)
                st.rerun()
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
            b_sel = st.selectbox("Batalha destino:", listar_batalhas_ativas(), format_func=lambda x: x['titulo'])
            modo = st.radio("Método:", ["Manual", "Via IA"], horizontal=True)

            if modo == "Manual":
                with st.form("form_manual"):
                    enun = st.text_area("Enunciado:")
                    a1, a2 = st.text_input("Alternativa A"), st.text_input("Alternativa B")
                    a3, a4 = st.text_input("Alternativa C"), st.text_input("Alternativa D")
                    correta = st.selectbox("Correta:", ["A", "B", "C", "D"], format_func=lambda x: f"Alternativa {x}")
                    if st.form_submit_button("Salvar Questão"):
                        res = cadastrar_questao_rapida(b_sel['id'], enun, [a1, a2, a3, a4], correta)
                        if res["sucesso"]: st.success("Salvo!"); st.rerun()
                        else: st.error(res["mensagem"])
            
            else: # --- IMPLEMENTAÇÃO IA ---
                arquivo = st.file_uploader("Upload de Caderno (PDF/DOCX)", type=["pdf", "docx"])
                prompt_custom = st.text_input("Instruções adicionais para a IA (opcional):")
                
                if arquivo and st.button("🤖 Processar e Injetar Questões"):
                    with st.spinner("Processando arquivo e gerando questões com IA..."):
                        ext = arquivo.name.split('.')[-1]
                        texto = extrair_texto_de_arquivo(arquivo.getvalue(), ext)
                        questoes = gerar_questoes_ia(texto, prompt_custom, st.secrets["GEMINI_API_KEY"])
                        
                        if questoes:
                            res = salvar_questoes_lote_ia(b_sel['id'], questoes)
                            if res["sucesso"]: st.success("Questões injetadas!"); st.rerun()
                            else: st.error(res["mensagem"])
                        else: st.warning("A IA não conseguiu extrair questões válidas.")

    # --- GESTÃO DE EQUIPES (ALUNOS) ---
    elif tipo_usuario == "aluno":
        if not aluno_tem_time(usuario_id):
            with st.expander("✨ Gerencie sua equipe:", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    nome = st.text_input("Nome da nova equipe:")
                    if st.button("🚀 Criar Equipe"): criar_time(nome); st.rerun()
                with c2:
                    times = listar_times()
                    if times:
                        sel = st.selectbox("Escolha uma equipe:", times, format_func=lambda x: x['nome'])
                        if st.button("🤝 Entrar"): entrar_no_time(sel['id'], usuario_id); st.rerun()
        else: st.success("✅ Você já está alocado em um time.")

    # --- ARENA DE BATALHAS ---
    todas = listar_batalhas_ativas()
    sinc, assinc = st.tabs(["⚡ Síncronas", "⏳ Assíncronas"])
    
    with sinc: renderizar_lista([b for b in todas if b.get("modalidade") == "sincrona"])
    with assinc: renderizar_lista([b for b in todas if b.get("modalidade") == "assincrona"])

def renderizar_lista(lista):
    if not lista: st.info("Nenhuma batalha ativa no momento."); return
    for ba in lista:
        with st.container(border=True):
            st.markdown(f"### {ba['titulo']}")
            
            # Botões Docentes
            if st.session_state.get("usuario_logado", {}).get("tipo_usuario") in ("professor", "admin"):
                col1, col2, col3 = st.columns(3)
                if col1.button("🚀 Iniciar", key=f"init_{ba['id']}"):
                    st.rerun()
                if col2.button("🛑 Encerrar", key=f"end_{ba['id']}"):
                    from services.batalha_service import encerrar_partida_sincrona
                    encerrar_partida_sincrona(ba['id']); st.rerun()
                if col3.button("🗑️ Deletar", key=f"del_{ba['id']}"):
                    deletar_batalha(ba['id']); st.rerun()
            
            if st.button(f"Entrar na Arena", key=f"entrar_{ba['id']}", use_container_width=True):
                st.session_state.batalha_ativa_id = ba["id"]; st.session_state.pagina = "batalha_rodada"; st.rerun()