import streamlit as st
import time
import datetime
from services.mini_prova_service import listar_mini_provas
from utils.compartilhamento import exibir_painel_compartilhamento
from utils.estilo import aplicar_estilo, cabecalho
from database.conexao import supabase

def tela_mini_provas():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()
    
    # Gerenciamento de estado para Acessibilidade
    if "alto_contraste" not in st.session_state:
        st.session_state.alto_contraste = False

    if st.session_state.alto_contraste:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: black;
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    cabecalho("Mini-provas", "Realize as provas disponíveis e modularizadas")

    # 👑 INTERCEPTADOR DO PROFESSOR: Atalho de gerenciamento direto no escopo da tela
    if tipo_usuario == "professor":
        st.markdown("### 🛠️ Painel de Controle Docente")
        if st.button("➕ Criar Nova Mini Prova ou Fazer Upload (PDF / WORD)", type="primary", use_container_width=True):
            st.session_state.pagina = "mini_provas_professor"
            st.rerun()
        st.divider()

    # 🎛️ Botões Superiores de Navegação (Visão Geral - Adaptada por Perfil)
    col1, col2, col3 = st.columns(3)

    with col1:
        texto_botao_pontos = "🏅 Ranking de Pontuação" if tipo_usuario == "professor" else "🏅 Minha Pontuação"
        if st.button(texto_botao_pontos, use_container_width=True):
            st.session_state.pagina = "pontuacoes" if tipo_usuario == "professor" else "pontuacao_mini_provas"
            st.rerun()

    with col2:
        texto_botao_desempenho = "📊 Desempenho dos Alunos" if tipo_usuario == "professor" else "📊 Meu Desempenho"
        if st.button(texto_botao_desempenho, use_container_width=True):
            st.session_state.pagina = "desempenho_mini_provas"
            st.rerun()

    with col3:
        with st.popover("⚙️ Acessibilidade", use_container_width=True):
            alto = st.checkbox("Alto contraste", value=st.session_state.alto_contraste)
            st.session_state.alto_contraste = alto
            st.checkbox("Leitura por questão")
            st.divider()
            st.subheader("Solicitar tempo extra")
            if st.button("Enviar solicitação", use_container_width=True):
                st.success("Solicitação enviada com sucesso!")

    st.divider()

    # Consome a lista limpa diretamente do service relacional
    mini_provas = listar_mini_provas()
    
    # 🕒 CHECAGEM TEMPORAL DE EXPIRAÇÃO AUTOMÁTICA (PRAZO Y)
    agora_atual = datetime.datetime.now()
    
    provas_filtradas_por_tempo = []
    for p in mini_provas:
        data_exp_str = p.get("data_expiracao")
        if data_exp_str:
            try:
                # Faz o parse removendo offsets se houver, para comparar localmente de forma segura
                data_exp = datetime.datetime.fromisoformat(data_exp_str.split("+")[0])
                if agora_atual > data_exp and p.get("status") == "Disponível":
                    # O tempo de vida Y esgotou! Inativa silenciosamente no banco de dados
                    supabase.table("mini_provas").update({"status": "Indisponível"}).eq("id", p["id"]).execute()
                    p["status"] = "Indisponível"
            except Exception:
                pass
                
        if p.get("status") == "Disponível":
            provas_filtradas_por_tempo.append(p)

    # ============================================================================
    # 🔍 SEÇÃO CONDICIONAL DE FILTROS E HISTÓRICO (ALUNO vs PROFESSOR)
    # ============================================================================
    if tipo_usuario == "aluno":
        pesquisa = st.text_input("🔍 Pesquisar mini prova por título:")
        if pesquisa:
            provas_filtradas_por_tempo = [p for p in provas_filtradas_por_tempo if pesquisa.lower() in str(p.get("titulo", "")).lower()]

        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.markdown("### 📋 Provas Ativas")
        with col_dir:
            if st.button("📜 Ver Meus Resultados (Histórico)", use_container_width=True):
                st.session_state.pagina = "resultados_mini_provas"
                st.rerun()
    else:
        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.markdown("### 📋 Provas Ativas")
        with col_dir:
            if st.button("📜 Ver Histórico Geral de Provas Encerradas", use_container_width=True):
                st.session_state.pagina = "historico_provas_professor"
                st.rerun()

    # ============================================================================

    if not provas_filtradas_por_tempo:
        st.info("💡 Nenhuma mini prova em andamento ou dentro do prazo de disponibilidade no momento.")
        return

    # 🎯 Renderização dos Cards Reativos das Provas Ativas e Dentro do Prazo
    for prova in provas_filtradas_por_tempo:
        with st.container(border=True):
            
            # Formata a data de exibição para dar visibilidade do prazo aos usuários
            data_exp_raw = prova.get("data_expiracao")
            prazo_exibicao = ""
            if data_exp_raw:
                try:
                    dt_p = datetime.datetime.fromisoformat(data_exp_raw.split("+")[0])
                    prazo_exibicao = f"&nbsp;|&nbsp; ⏳ Disponível até: {dt_p.strftime('%d/%m às %H:%M')}"
                except:
                    pass

            st.markdown(f"""
            <div style="background:#f0f9ff; border-left:4px solid #00b4d8; border-radius:8px; padding:14px 18px; margin-bottom:10px;">
                <strong style="color:#0d1b2a; font-size:16px;">{prova.get('titulo', 'Sem Título')}</strong><br>
                <span style="color:#555; font-size:13px;">{prova.get('descricao', 'Sem descrição definida para este exame.')}</span><br>
                <span style="color:#00b4d8; font-size:12px; font-weight:600;">
                    📝 {prova.get('quantidade_questoes', '-')} Questões &nbsp;|&nbsp; ⏱️ Tempo de Resolução: {prova.get('duracao_minutos', '-')} min {prazo_exibicao}
                </span>
            </div>
            """, unsafe_allow_html=True)

            if tipo_usuario == "aluno":
                if st.button(f"🎯 Iniciar Avaliação", key=f"run_p_{prova['id']}", type="primary", use_container_width=True):
                    st.session_state.prova_ativa_id = prova["id"]
                    st.session_state.pagina = "realizar_mini_prova"
                    st.rerun()
            else:
                # 👑 VISÃO DOCENTE: Compartilhamento + Controle de Encerramento Antecipado
                col_comp, col_fechar = st.columns([2, 1])
                
                with col_comp:
                    with st.expander("📢 Links de Acesso Direto & QR Code", expanded=False):
                        exibir_painel_compartilhamento(tipo_sala="prova", sala_id=prova["id"])
                
                with col_fechar:
                    if st.button("🔴 Finalizar Antes", key=f"close_p_{prova['id']}", use_container_width=True):
                        try:
                            supabase.table("mini_provas").update({"status": "Indisponível"}).eq("id", prova["id"]).execute()
                            st.success("Avaliação finalizada! Movendo para o histórico...")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao encerrar: {e}")