import streamlit as st
import qrcode
from io import BytesIO

def obter_url_base():
    """
    Detecta dinamicamente o domínio do app em produção ou fallback para localhost.
    """
    url_cloud = st.secrets.get("URL_PRODUCAO")
    if url_cloud:
        return url_cloud.strip("/")
    return "http://localhost:8501"

def gerar_qr_code(url_destino):
    """
    Monta a matriz de dados do QR Code diretamente em memória buffer.
    """
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

def exibir_painel_compartilhamento(tipo_sala, sala_id):
    """
    Renderiza um componente visual elegante contendo link, botão e o QR Code de escaneamento.
    """
    url_base = obter_url_base()
    url_completa = f"{url_base}/?sala={tipo_sala}&id={sala_id}"
    
    st.markdown("#### 📢 Link de Acesso e Entrada Direta")
    col_link, col_qr = st.columns([2, 1])
    
    with col_link:
        st.markdown("**URL da Sala:**")
        st.code(url_completa, language="text")
        st.markdown(f"[🔗 Abrir Sala em Nova Aba]({url_completa})")
        st.caption("Partilhe este link com a turma no chat da aula ou grupo de estudos.")
        
    with col_qr:
        st.markdown("**Acesso via Telemóvel:**")
        qr_bytes = gerar_qr_code(url_completa)
        st.image(qr_bytes, width=150)