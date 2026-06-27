import streamlit as st
from supabase import create_client

url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase_url")
key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase_key")

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

supabase = create_client(url, key)