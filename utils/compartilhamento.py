import streamlit as st
import qrcode
from io import BytesIO

def obter_url_base():
    """Detecta dinamicamente o domínio do app em produção ou fallback para localhost."""
    url_cloud = st.secrets.get("URL_PRODUCAO")
    if url_cloud:
        return url_cloud.strip("/")
    return "http://localhost:8501"

def gerar_qr_code(url_destino):
    """Monta a matriz de dados do QR Code diretamente em memória buffer."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_destino)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def exibir_painel_compartilhamento(desafio_id):
    """
    Renderiza o componente visual para o professor compartilhar o desafio específico.
    Adequado para uso na tela de listagem de desafios.
    """
    url_base = obter_url_base()
    # Adequado para passar o parâmetro desafio_id
    url_completa = f"{url_base}/?desafio_id={desafio_id}"
    
    st.markdown("#### 📢 Partilhar Desafio Operacional")
    col_link, col_qr = st.columns([2, 1])
    
    with col_link:
        st.markdown("**URL Direta do Desafio:**")
        st.code(url_completa, language="text")
        st.markdown(f"[🔗 Abrir Desafio em Nova Aba]({url_completa})")
        st.caption("Distribua este link ou utilize o QR Code ao lado na projeção em sala.")
        
    with col_qr:
        st.markdown("**Acesso via Telemóvel:**")
        qr_bytes = gerar_qr_code(url_completa)
        st.image(qr_bytes, width=150)