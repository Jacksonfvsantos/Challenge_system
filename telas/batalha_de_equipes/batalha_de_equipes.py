import streamlit as st
from datetime import datetime
from utils.estilo import aplicar_estilo, cabecalho
from services.batalha_service import listar_batalhas_ativas

def tela_batalha_de_equipes():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    cabecalho(
        "⚔️ Arena de Batalha de Equipes", 
        "Participe de rodadas síncronas e desafios de engenharia"
    )

    batalhas = listar_batalhas_ativas()
    agora = datetime.now()

    if not batalhas:
        st.info("Nenhuma batalha ativa no momento.")

    for ba in batalhas:
        with st.container(border=True):
            col_info, col_a_action = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"### {ba['titulo']}")
                st.write(ba.get("descricao", "Sem diretrizes anexadas."))
                

                prazo_str = ba.get("data_limite")
                expirada = False
                
                if prazo_str:
                    try:
                        prazo_dt = datetime.fromisoformat(prazo_str.replace("Z", ""))
                        exibicao_data = prazo_dt.strftime('%d/%m/%Y às %H:%M')
                        
                        if agora > prazo_dt:
                            st.markdown(f"🛑 <span style='color:#ef4444; font-weight:bold;'>Prazo Encerrado: {exibicao_data}</span>", unsafe_allow_html=True)
                            expirada = True
                        else:
                            st.markdown(f"📅 <span style='color:#10b981; font-weight:bold;'>Entregar até: {exibicao_data}</span>", unsafe_allow_html=True)
                    except ValueError:
                        st.caption("📅 Data limite com formato inválido.")
                else:
                    st.caption("📅 Sem prazo restritivo definido pelo docente.")

            with col_a_action:
                st.markdown("<br>", unsafe_allow_html=True)
                btn_label = "Prazo Bloqueado" if expirada else "Enviar Solução"
                
                if st.button(btn_label, key=f"sub_{ba['id']}", type="secondary", use_container_width=True, disabled=expirada):
                    st.session_state.batalha_ativa_id = ba["id"]
                    st.session_state.pagina = "batalha_rodada"
                    st.rerun()

    # Painel de Governança
    if tipo_usuario in ("professor", "admin"):
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### 🛠️ Painel Advanced de Governança Docente")
        st.caption("Ações de bastidores para provisionar equipes, ajustar integrantes e criar novos editais.")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        if col_m1.button("🏢 Gerenciar Equipes", use_container_width=True):
            st.session_state.pagina = "batalha_times"
            st.rerun()
        if col_m2.button("👥 Alocação de Alunos", use_container_width=True):
            st.session_state.pagina = "batalha_integrantes"
            st.rerun()
        if col_m3.button("📝 Abrir Nova Batalha", type="primary", use_container_width=True):
            st.session_state.pagina = "batalha_gerenciar"
            st.rerun()