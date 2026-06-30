import streamlit as st

def iniciar_session():
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None

    if "pagina" not in st.session_state:
        st.session_state.pagina = "login"
        
    if "tipo_usuario" not in st.session_state:
        st.session_state.tipo_usuario = "aluno"

    if "alto_contraste" not in st.session_state:
        st.session_state.alto_contraste = False

def obter_usuario_atual():
    usuario = st.session_state.get("usuario_logado") or {}
    return {
        "id": str(usuario.get("id", "")).strip(),
        "nome": usuario.get("nome", "Usuário"),
        "email": usuario.get("email", ""),
        "tipo": str(usuario.get("tipo_usuario", "aluno")).strip().lower(),
        "logado": bool(usuario.get("id"))
    }