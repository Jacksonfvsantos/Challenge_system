import streamlit as st
import datetime
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.desafio_service import listar_desafios, criar_desafio
from services.participacao_service import (
    participar_desafio,
    listar_participantes,
    concluir_desafio,
    cancelar_participacao
)

def formatar_data_br(data_str):
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
        "🎯 Central de Desafios Práticos", 
        "Resolva Problemas reais, submeta suas soluções e ganhe pontos para subir no Ranking Geral"
    )

    if tipo_usuario in ("professor", "admin"):
        aba_lista, aba_cadastro = st.tabs(["📋 Desafios Lançados", "✨ Cadastrar Novo Desafio"])
    else:
        aba_lista = st.container()
        aba_cadastro = None

    if aba_cadastro:
        with aba_cadastro:
            st.markdown("### ➕ Criar Novo Desafio Prático")
            st.caption("Preencha as diretrizes abaixo. O sistema disparará alertas automáticos para a turma.")
            
            with st.form("form_novo_desafio_modular", clear_on_submit=True):
                titulo = st.text_input("Título do Desafio:", placeholder="Ex: Otimização de Consultas SQL Complexas")
                descricao = st.text_area("Enunciado / Requisitos Técnicos:", placeholder="Descreva detalhadamente o escopo, arquitetura alvo e critérios de aceitação...")
                
                col_n, col_d = st.columns(2)
                nivel = col_n.selectbox("Nível de Complexidade:", ["Fácil", "Intermediário", "Difícil"])
                data_limite = col_d.date_input("Data Limite de Entrega:", min_value=datetime.date.today())
                
                st.markdown("<br>", unsafe_allow_html=True)
                btn_publicar = st.form_submit_button("🔥 Publicar Desafio para a Arena", use_container_width=True)
                
                if btn_publicar:
                    if not titulo.strip() or not descricao.strip():
                        st.error("🛑 **Erro de Validação:** O título e o enunciado técnico são obrigatórios.")
                    else:
                        with st.spinner("Registrando escopo e notificando estudantes..."):
                            res = criar_desafio(titulo, descricao, usuario_id, str(data_limite), nivel)
                            if res.get("sucesso"):
                                st.success("🎉 Desafio cadastrado com sucesso! Uma notificação de sistema foi enviada para todos os alunos.")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(f"❌ Falha operacional ao salvar no banco: {res.get('mensagem')}")

    with aba_lista:
        desafios_ativos = listar_desafios() or []
        
        if not desafios_ativos:
            st.info("💡 Nenhum desafio operacional ativo no ecossistema neste momento. Aguarde as diretrizes do professor.")
        else:
            for desafio in desafios_ativos:
                desafio_id = desafio.get("id")
                prazo_br = formatar_data_br(desafio.get("data_limite"))
                nivel_badge = desafio.get("nivel_dificuldade", "N/A")
                
                with st.container(border=True):
                    st.markdown(f"### 🎯 {desafio.get('titulo', 'Sem Título')}")
                    st.write(desafio.get("descricao", "Sem descrição disponível."))
                    st.markdown(f"**📊 Nível:** `{nivel_badge}` &nbsp;|&nbsp; **📅 Prazo Final (BR):** `{prazo_br}`")
                    
                    if tipo_usuario == "aluno":
                        participantes = listar_participantes(desafio_id) or []
                        vinc_aluno = next((p for p in participantes if str(p.get("usuario_id")).strip() == usuario_id), None)
                        
                        st.write("")
                        if not vinc_aluno:
                            if st.button("🚀 Ingressar e Iniciar Desafio", key=f"ing_{desafio_id}", type="primary", use_container_width=True):
                                if participar_desafio(desafio_id, usuario_id):
                                    st.toast("Inscrição confirmada! Bons códigos.", icon="💻")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Erro ao processar inscrição no desafio.")
                        
                        elif vinc_aluno.get("status") == "participando":
                            col_c1, col_c2 = st.columns(2)
                            with col_c1:
                                if st.button("🏁 Concluir e Submeter Solução", key=f"conc_{desafio_id}", type="primary", use_container_width=True):
                                    concluir_desafio(desafio_id, usuario_id)
                                    st.toast("Desafio concluído com sucesso! XP em processamento.", icon="🏆")
                                    time.sleep(0.5)
                                    st.rerun()
                            with col_c2:
                                if st.button("❌ Cancelar Minha Inscrição", key=f"canc_{desafio_id}", type="secondary", use_container_width=True):
                                    cancelar_participacao(desafio_id, usuario_id)
                                    st.toast("Inscrição removida do seu painel.", icon="⚠️")
                                    time.sleep(0.5)
                                    st.rerun()
                                    
                        elif vinc_aluno.get("status") == "concluido":
                            st.success("👑 **Desafio Concluído!** Sua entrega foi registrada com sucesso e já está disponível para o fórum de avaliação e votos.")

                    elif tipo_usuario in ("professor", "admin"):
                        participantes = listar_participantes(desafio_id) or []
                        total_inscritos = len(participantes)
                        total_concluidos = sum(1 for p in participantes if p.get("status") == "concluido")
                        
                        st.write("")
                        exp_auditoria = st.expander(f"📊 Relatório de Engajamento ({total_inscritos} Alunos Inscritos | {total_concluidos} Concluíram)")
                        with exp_auditoria:
                            if not participantes:
                                st.caption("Nenhum aluno se inscreveu neste desafio acadêmico até o momento.")
                            else:
                                for p in participantes:
                                    nome_estudante = p.get("usuarios", {}).get("nome", "Usuário")
                                    status_cru = p.get("status", "participando")
                                    emoji_status = "🟢 [Concluído]" if status_cru == "concluido" else "🟡 [Em Progresso]"
                                    st.markdown(f"{emoji_status} **{nome_estudante}**")

                    # --- INTEGRAÇÃO DO QR CODE (REQUISITO DE RELATÓRIO) ---
                    if tipo_usuario in ("professor", "admin"):
                        with st.expander("📡 Painel de Compartilhamento (QR Code / Link)"):
                            from utils.compartilhamento import exibir_painel_compartilhamento
                            exibir_painel_compartilhamento("desafio", desafio_id)