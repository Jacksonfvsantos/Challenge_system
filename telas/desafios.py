import streamlit as st
import datetime
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.desafio_service import listar_desafios, criar_desafio, deletar_desafio
from services.participacao_service import (
    participar_desafio,
    listar_participantes,
    concluir_desafio,
    cancelar_participacao
)

def formatar_data_br(data_str):
    """Converte datas padrão ISO (YYYY-MM-DD) para o formato brasileiro (DD/MM/YYYY)"""
    if not data_str:
        return "Sem prazo informado"
    try:
        data_limpa = data_str.split("T")[0]
        ano, mes, dia = data_limpa.split("-")
        return f"{dia}/{mes}/{ano}"
    except Exception:
        return data_str

def tela_desafios():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho(
        "🎯 Central de Desafios Operacionais", 
        "Participe de projetos práticos da engenharia, submeta soluções robustas e eleve seu XP"
    )

    if tipo_usuario in ("professor", "admin"):
        aba_lista, aba_cadastro = st.tabs(["📋 Desafios Lançados", "✨ Cadastrar Novo Desafio"])
    else:
        aba_lista = st.container()
        aba_cadastro = None

    # --- ABA DE CADASTRO (EXCLUSIVA DO DOCENTE) ---
    if aba_cadastro:
        with aba_cadastro:
            st.markdown("### ➕ Criar Novo Desafio Prático")
            with st.form("form_novo_desafio_modular", clear_on_submit=True):
                titulo = st.text_input("Título do Desafio:", placeholder="Ex: Otimização de Consultas SQL")
                descricao = st.text_area("Enunciado / Requisitos Técnicos:", placeholder="Descreva os requisitos...")
                
                col_n, col_d = st.columns(2)
                nivel = col_n.selectbox("Nível de Complexidade:", ["Fácil", "Intermediário", "Difícil"])
                data_limite = col_d.date_input("Data Limite de Entrega:", min_value=datetime.date.today())
                
                btn_publicar = st.form_submit_button("🔥 Publicar Desafio", use_container_width=True)
                
                if btn_publicar:
                    if not titulo.strip() or not descricao.strip():
                        st.error("🛑 Título e Enunciado são obrigatórios!")
                    else:
                        with st.spinner("Publicando desafio..."):
                            res = criar_desafio(titulo, descricao, usuario_id, str(data_limite), nivel)
                            if res.get("sucesso"):
                                st.success("🎉 Desafio cadastrado com sucesso!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(f"❌ Erro ao salvar: {res.get('mensagem')}")

    # --- ABA DE LISTAGEM ---
    with aba_lista:
        desafios_ativos = listar_desafios() or []
        
        if not desafios_ativos:
            st.info("Nenhum desafio operacional ativo no momento.")
        else:
            for desafio in desafios_ativos:
                desafio_id = desafio.get("id")
                prazo_br = formatar_data_br(desafio.get("data_limite"))
                
                with st.container(border=True):
                    st.markdown(f"### 🎯 {desafio.get('titulo', 'Sem Título')}")
                    st.write(desafio.get("descricao", "Sem descrição."))
                    st.markdown(f"**📊 Nível:** `{desafio.get('nivel_dificuldade')}` &nbsp;|&nbsp; **📅 Prazo Final:** `{prazo_br}`")
                    
                    # Fluxo do Aluno
                    if tipo_usuario == "aluno":
                        participantes = listar_participantes(desafio_id) or []
                        vinc_aluno = next((p for p in participantes if str(p.get("usuario_id")).strip() == usuario_id), None)
                        
                        if not vinc_aluno:
                            if st.button("🚀 Ingressar no Desafio", key=f"ing_{desafio_id}", type="primary", use_container_width=True):
                                if participar_desafio(desafio_id, usuario_id): st.rerun()
                        elif vinc_aluno.get("status") == "participando":
                            with st.expander("🏁 Concluir e Submeter Entrega"):
                                submissao_texto = st.text_area("Cole aqui o link do seu projeto ou suas observações:", key=f"sub_{desafio_id}")
                                
                                col_c1, col_c2 = st.columns(2)
                                
                                if col_c1.button("✅ Enviar e Concluir", key=f"conc_{desafio_id}", type="primary", use_container_width=True):
                                    if not submissao_texto.strip():
                                        st.error("Por favor, preencha a submissão antes de concluir.")
                                    else:
                                        if concluir_desafio(desafio_id, usuario_id, submissao_texto):
                                            st.toast("Sucesso! Desafio entregue.")
                                            time.sleep(1)
                                            st.rerun()
                                            
                                if col_c2.button("❌ Cancelar", key=f"canc_{desafio_id}", type="secondary", use_container_width=True):
                                    cancelar_participacao(desafio_id, usuario_id)
                                    st.rerun()
                                    
                        elif vinc_aluno.get("status") == "concluido":
                            st.success("👑 Desafio Concluído!")
                            if vinc_aluno.get("submissao"): st.info(f"🔗 Sua entrega: {vinc_aluno.get('submissao')}")

                    # Fluxo do Docente
                    elif tipo_usuario in ("professor", "admin"):
                        if st.button("🗑️ Excluir Desafio Definitivamente", key=f"del_{desafio_id}", type="primary", use_container_width=True):
                            if deletar_desafio(desafio_id):
                                st.success("Desafio removido!"); st.rerun()
                            else:
                                st.error("Erro ao excluir.")
                        
                        participantes = listar_participantes(desafio_id) or []
                        with st.expander(f"📊 Ver inscritos ({len(participantes)})"):
                            for p in participantes:
                                st.markdown(f"• **{p.get('usuarios', {}).get('nome', 'Alu')}** - `{p.get('status')}`")
                                if p.get("submissao"): st.caption(f"🔗 Entrega: {p.get('submissao')}")