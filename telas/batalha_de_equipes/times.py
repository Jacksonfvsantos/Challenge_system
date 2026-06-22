import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho
from database.conexao import supabase
from services.batalha_service import aluno_criar_e_entrar_no_time, aluno_sair_do_time

def obter_time_atual_aluno(usuario_id):
    try:
        res = supabase.table("time_membros").select("time_id, times(nome)").eq("usuario_id", usuario_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def tela_batalha_times():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    
    cabecalho("🏢 Central de Equipes", "Gerencie sua filiação em times para a rodada síncrona")

    # Busca se o aluno já pertence a algum grupo
    vinculo_atual = obter_time_atual_aluno(usuario_id)

    # ------------------------------------------------------------------------
    # FLUXO A: ALUNO JÁ POSSUI UM TIME ATIVO
    # ------------------------------------------------------------------------
    if vinculo_atual:
        nome_time = vinculo_atual.get("times", {}).get("nome", "Equipe sem nome")
        
        with st.container(border=True):
            st.markdown(f"### 🛡️ Sua Equipe: <span style='color:#10b981;'>{nome_time}</span>", unsafe_allow_html=True)
            st.write("Você está devidamente alocado e pronto para receber perguntas na arena síncrona.")
            st.caption("Nota: Para entrar em outra equipe, você precisa se desligar da atual primeiro.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Botão de desvinculação (Sair do Time)
            if st.button("🚨 Abandonar / Sair da Equipe", type="primary", use_container_width=True):
                retorno = aluno_sair_do_time(usuario_id)
                if retorno["sucesso"]:
                    st.success(retorno["mensagem"])
                    st.rerun()
                else:
                    st.error(retorno["mensagem"])

    # ------------------------------------------------------------------------
    # FLUXO B: ALUNO ESTÁ SEM TIME (LIBERA FORMULÁRIO DE CRIAÇÃO)
    # ------------------------------------------------------------------------
    else:
        st.warning("⚠️ Você não pertence a nenhuma equipe no momento. Crie uma abaixo para poder pontuar.")
        
        with st.form("form_registro_time", clear_on_submit=True):
            st.markdown("#### ✨ Fundar Nova Equipe")
            novo_nome_time = st.text_input("Nome da Equipe:", placeholder="Ex: Computaloucos", max_chars=50)
            
            btn_criar = st.form_submit_button("Gravar e Ativar Equipe", type="primary", use_container_width=True)
            
            if btn_criar:
                if not novo_nome_time.strip():
                    st.error("O nome da equipe não pode ficar em branco.")
                elif len(novo_nome_time.strip()) < 3:
                    st.error("O nome da equipe deve ter no mínimo 3 caracteres.")
                else:
                    # Executa a operação transacional
                    resultado = aluno_criar_e_entrar_no_time(novo_nome_time, usuario_id)
                    
                    if resultado["sucesso"]:
                        st.success(resultado["mensagem"])
                        st.rerun()
                    else:
                        st.error(resultado["mensagem"])

    # Botão de retorno para a Arena principal
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Voltar para a Arena", use_container_width=True):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()
