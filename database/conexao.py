import streamlit as st
from supabase import create_client

# 🚀 Carrega as credenciais administrativas (Service Role) diretamente dos Secrets do Streamlit
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except Exception as e:
    raise Exception(
        "Erro ao carregar as credenciais do Streamlit Secrets. "
        "Certifica-te de que configuraste SUPABASE_URL e SUPABASE_KEY no painel do Streamlit Cloud."
    ) from e

if not url or not key:
    raise Exception(
        "Credenciais do Supabase não encontradas. "
        "Verifica as variáveis SUPABASE_URL e SUPABASE_KEY dentro do st.secrets."
    )

# Inicialização limpa, única e global do cliente do Supabase
supabase = create_client(url, key)