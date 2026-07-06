import streamlit as st
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import (
    listar_batalhas_ativas, 
    cadastrar_nova_batalha, 
    deletar_batalha, 
    listar_times, 
    deletar_time,
    listar_membros_time,
    obter_batalhas_finalizadas
)

def tela_batalha_de_equipes():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho("⚔️ Arena de Batalha de Equipes", "Participe de desafios síncronos e assíncronos em tempo real")

    # --- MENU DE NAVEGAÇÃO RÁPIDA ---
    st.write("")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("👥 Minha Equipe / Central de Times", use_container_width=True, key="btn_nav_times"):
            st.session_state.pagina = "batalha_times"
            st.rerun()
    with col_nav2:
        if tipo_usuario in ("professor", "admin"):
            if st.button("🛠️ Gestão Avançada de Integrantes", use_container_width=True, key="btn_nav_integrantes"):
                st.session_state.pagina = "batalha_integrantes"
                st.rerun()

    st.divider()

    # --- GOVERNANÇA DOCENTE ---
    if tipo_usuario in ("professor", "admin"):
        with st.expander("👨‍🏫 Governança Docente (Painel do Professor)", expanded=False):
            aba_g1, aba_g2 = st.tabs(["➕ Lançar Nova Arena", "🤝 Gerenciar Equipes"])
            
            with aba_g1:
                with st.form("form_nova_batalha", clear_on_submit=True):
                    titulo_b = st.text_input("Título da Batalha:")
                    desc_b = st.text_area("Instruções Técnicas:")
                    mod_b = st.selectbox("Modalidade:", ["sincrona", "assincrona"])
                    
                    times_b = listar_times()
                    options_times = [t["id"] for t in times_b]
                    format_time = lambda x: next((t["nome"] for t in times_b if t["id"] == x), "Selecione")
                    
                    t_a = st.selectbox("Equipe Alfa:", options=options_times, format_func=format_time)
                    t_b = st.selectbox("Equipe Beta:", options=options_times, format_func=format_time)
                    
                    if st.form_submit_button("🚀 Fundar Arena de Batalha"):
                        if not titulo_b.strip():
                            st.error("O título da arena é obrigatório.")
                        elif t_a == t_b:
                            st.error("Uma equipe não pode batalhar contra si mesma.")
                        else:
                            res = cadastrar_nova_batalha(titulo_b, desc_b, t_a, t_b, mod_b)
                            if res.get("sucesso"):
                                st.success("Nova arena cadastrada com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(res.get("mensagem"))
                                
            with aba_g2:
                st.markdown("#### Lista de Equipes Cadastradas")
                todos_times = listar_times()
                if not todos_times:
                    st.caption("Nenhum time registrado no ecossistema.")
                else:
                    for time_item in todos_times:
                        with st.expander(f"Time: {time_item['nome']}"):
                            if st.button("Excluir Time", key=f"del_t_{time_item['id']}", type="primary"):
                                if deletar_time(time_item['id']):
                                    st.success("Time excluído!")
                                    time.sleep(0.5)
                                    st.rerun()
                            
                            membros = listar_membros_time(time_item['id'])
                            for m in membros:
                                m_id = m.get("id")
                                st.markdown(f"• {m['nome']} ({m['email']})")

    # --- LISTAGEM DE ARENAS POR ABAS ---
    aba_sinc, aba_assinc, aba_hist_sinc, aba_hist_assinc = st.tabs([
        "⚡ Síncronas", "⏳ Assíncronas", "📜 Hist. Síncronas", "📜 Hist. Assíncronas"
    ])

    batalhas_ativas = listar_batalhas_ativas()
    batalhas_finalizadas = obter_batalhas_finalizadas()

    ativas_sinc = [b for b in batalhas_ativas if b.get("modalidade") == "sincrona"]
    ativas_assinc = [b for b in batalhas_ativas if b.get("modalidade") == "assincrona"]
    fin_sinc = [b for b in batalhas_finalizadas if b.get("modalidade") == "sincrona"]
    fin_assinc = [b for b in batalhas_finalizadas if b.get("modalidade") == "assincrona"]

    with aba_sinc:
        if not ativas_sinc:
            st.info("Nenhuma batalha ativa.")
        else:
            for b in ativas_sinc:
                with st.container(border=True):
                    st.markdown(f"### ⚔️ {b['titulo']}")
                    st.write(b.get("descricao", "Sem descrição."))
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("🎯 Entrar na Arena Ao Vivo", key=f"entrar_sinc_{b['id']}", type="primary", use_container_width=True):
                            st.session_state.batalha_ativa_id = b["id"]
                            st.session_state.pagina = "batalha_rodada_sincrona"
                            st.rerun()
                    with col_b2:
                        if tipo_usuario in ("professor", "admin"):
                            if st.button("🗑️ Cancelar Arena", key=f"del_sinc_{b['id']}", use_container_width=True):
                                if deletar_batalha(b["id"]):
                                    st.rerun()
                    
                    # --- INTEGRAÇÃO DO QR CODE (REQUISITO DE RELATÓRIO) ---
                    if tipo_usuario in ("professor", "admin"):
                        with st.expander("📡 Painel de Compartilhamento (QR Code / Link)"):
                            from utils.compartilhamento import exibir_painel_compartilhamento
                            exibir_painel_compartilhamento("batalha", b["id"])

    with aba_assinc:
        if not ativas_assinc:
            st.info("Nenhuma batalha ativa.")
        else:
            for b in ativas_assinc:
                with st.container(border=True):
                    st.markdown(f"### ⏳ {b['titulo']}")
                    st.write(b.get("descricao", "Sem descrição."))
                    
                    col_ba1, col_ba2 = st.columns(2)
                    with col_ba1:
                        if st.button("🎯 Responder Missão Assíncrona", key=f"entrar_assinc_{b['id']}", type="primary", use_container_width=True):
                            st.session_state.batalha_ativa_id = b["id"]
                            st.session_state.pagina = "batalha_rodada_assincrona"
                            st.rerun()
                    with col_ba2:
                        if tipo_usuario in ("professor", "admin"):
                            if st.button("🗑️ Cancelar Arena", key=f"del_assinc_{b['id']}", use_container_width=True):
                                if deletar_batalha(b["id"]):
                                    st.rerun()
                                    
                    # --- INTEGRAÇÃO DO QR CODE (REQUISITO DE RELATÓRIO) ---
                    if tipo_usuario in ("professor", "admin"):
                        with st.expander("📡 Painel de Compartilhamento (QR Code / Link)"):
                            from utils.compartilhamento import exibir_painel_compartilhamento
                            exibir_painel_compartilhamento("batalha", b["id"])

    with aba_hist_sinc:
        if not fin_sinc:
            st.info("Nenhum histórico disponível.")
        else:
            for b in fin_sinc:
                with st.container(border=True):
                    st.markdown(f"#### 🏁 {b['titulo']}")
                    st.info(b.get("resultado_extenso", "Resultado arquivado"))

    with aba_hist_assinc:
        if not fin_assinc:
            st.info("Nenhum histórico disponível.")
        else:
            for b in fin_assinc:
                with st.container(border=True):
                    st.markdown(f"#### 🏁 {b['titulo']}")
                    st.info(b.get("resultado_extenso", "Resultado arquivado"))