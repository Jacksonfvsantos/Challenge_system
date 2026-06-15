import streamlit as st
from datetime import datetime
from services.desafio_service import listar_desafios, criar_desafio
from utils.estilo import aplicar_estilo, cabecalho

def formatar_data_br(data_str):
    """Converte uma data ISO (aaaa-mm-dd) para o formato brasileiro (dd/mm/aaaa)"""
    if not data_str or data_str == "Sem prazo":
        return "Sem prazo"
    try:
        # Tenta fatiar caso venha com timestamp do Supabase
        data_limpa = str(data_str).split("T")[0]
        dt = datetime.strptime(data_limpa, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_str

def tela_desafios():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    tipo_usuario = usuario.get("tipo_usuario", "aluno")
    usuario_id = usuario.get("id")

    cabecalho("Central de Desafios", "Explore os desafios de programação disponíveis ou crie novos.")

    # Inicialização do controle de abas ativo na sessão para permitir redirecionamento dinâmico
    if "aba_desafios_ativa" not in st.session_state:
        st.session_state["aba_desafios_ativa"] = 0

    if tipo_usuario == "professor":
         abas = st.tabs(["📋 Desafios Ativos", "✨ Criar Novo Desafio"])
    else:
         abas = st.tabs(["📋 Desafios Ativos"])

    # --- ABA 1: LISTAR DESAFIOS ---
    with abas[0]:
        st.subheader("Lista de Desafios")
        try:
            desafios = listar_desafios()
        except Exception:
            desafios = []

        if not desafios:
            st.info("Nenhum desafio disponível no momento.")
        else:
            for desafio in desafios:
                titulo = desafio.get('titulo', 'Sem Título')
                descricao = desafio.get('descricao', 'Sem descrição.')
                nivel = desafio.get("nivel_dificuldade") or desafio.get("nivel") or "Não informado"
                
                # CORREÇÃO CRÍTICA: Exibição no formato brasileiro solicitado (Item 2.22)
                prazo_cru = desafio.get('data_limite', 'Sem prazo')
                prazo_br = formatar_data_br(prazo_cru)

                st.markdown(f"""
                <div style="
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-left: 5px solid #1b3a5c;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <h3 style="margin-top: 0; color: #1b3a5c; font-size: 20px;">{titulo}</h3>
                    <p style="color: #333333; font-size: 14px; line-height: 1.5;">{descricao}</p>
                    <div style="display: flex; justify-content: space-between; margin-top: 15px; border-top: 1px solid #f0f0f0; padding-top: 10px;">
                        <span style="font-size: 12px; color: #666666;"><strong>Nível:</strong> {nivel}</span>
                        <span style="font-size: 12px; color: #666666; font-weight: bold;">📅 Prazo Limite: {prazo_br}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- ABA 2: CADASTRAR DESAFIO (PROFESSOR) ---
    if tipo_usuario == "professor":
        with abas[1]:
            st.subheader("Cadastrar Novo Desafio")
            
            # Inicialização de estados dos campos para permitir limpeza total controlada (Item 2.26)
            if "ins_titulo" not in st.session_state: st.session_state["ins_titulo"] = ""
            if "ins_desc" not in st.session_state: st.session_state["ins_desc"] = ""

            with st.form("form_novo_desafio", clear_on_submit=False):
                titulo_input = st.text_input("Título do Desafio", value=st.session_state["ins_titulo"])
                descricao_input = st.text_area("Descrição / Enunciado", value=st.session_state["ins_desc"])
                nivel_input = st.selectbox("Nível de Dificuldade", ["Fácil", "Médio", "Dificil"])
                data_limite_input = st.date_input("Data Limite de Entrega", value=datetime.today())
                
                enviado = st.form_submit_button("Salvar Desafio", use_container_width=True)
                
                if enviado:
                    if not titulo_input or not descricao_input:
                        st.error("Por favor, preencha o título e a descrição.")
                    else:
                        # Converte a data selecionada para string ISO antes de mandar para o Supabase
                        data_iso = data_limite_input.strftime("%Y-%m-%d")
                        res = criar_desafio(titulo_input, descricao_input, usuario_id, data_iso, nivel_input)
                        
                        if res.get("sucesso") or res.get("id") or isinstance(res, dict):
                            # FEEDBACK VISUAL DE SUCESSO (Item 2.25)
                            st.success("✅ Desafio criado com sucesso no servidor!")
                            
                            # LIMPEZA DO FORMULÁRIO (Item 2.26)
                            st.session_state["ins_titulo"] = ""
                            st.session_state["ins_desc"] = ""
                            
                            # REDIRECIONAMENTO AUTOMÁTICO PARA LISTAGEM (Item 2.27)
                            st.session_state["pagina"] = "desafios"
                            st.rerun()
                        else:
                            st.error(res.get("mensagem", "Erro ao tentar registrar o desafio."))