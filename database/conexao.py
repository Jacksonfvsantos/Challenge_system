import streamlit as st
from supabase import create_client

# 🚀 PROTEÇÃO CONTRA KEYERROR: Busca tolerante aceitando maiúsculas e minúsculas
url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase_url")
key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase_key")

# Validação limpa e explícita antes de instanciar o cliente do banco
if not url or not key:
    st.error("🛑 **Erro de Configuração:** Credenciais do Supabase não localizadas!")
    st.markdown("""
    Garante que configuraste as variáveis exatamente no painel de **Secrets** do Streamlit Cloud:
    ```toml
    SUPABASE_URL = "sua_url_aqui"
    SUPABASE_KEY = "sua_service_role_key_aqui"
    ```
    """)
    st.stop()

# Inicialização limpa, única e global do cliente do Supabase
supabase = create_client(url, key)