import streamlit as st

def aplicar_estilo():
    """
    Injeta o CSS customizado para corrigir a legibilidade da barra lateral
    e dos botoes do menu contra o fundo escuro.
    """
    st.markdown("""
        <style>
            /* 1. GARANTE O FUNDO ESCURO DA NAVBAR LATERAL */
            [data-testid="stSidebar"] {
                background-color: #0d1b2a !important;
            }

            /* 2. FORÇA TEXTOS, PARÁGRAFOS E TEXTOS DE LINKS PARA BRANCO */
            [data-testid="stSidebar"] .stMarkdown p,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] a {
                color: #ffffff !important;
                text-decoration: none !important;
            }

            /* 3. ESTILIZA OS BOTÕES DO MENU (ST.BUTTON) DENTRO DA NAVBAR */
            [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
                background-color: #1b3a5c !important;
                color: #ffffff !important;
                border: 1px solid #00b4d8 !important;
                border-radius: 6px !important;
                transition: all 0.3s ease;
                width: 100% !important;
                display: block !important;
            }

            /* 4. EFEITO HOVER - COR DO BOTÃO AO PASSAR O MOUSE (INVERTE PARA CONTRASTE) */
            [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
                background-color: #00b4d8 !important;
                color: #0d1b2a !important;
                border-color: #ffffff !important;
                cursor: pointer;
            }

            /* 5. GARANTE QUE OS TEXTOS DE DENTRO DOS BOTÕES FIQUEM BRANCOS POR PADRÃO */
            [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] p {
                color: #ffffff !important;
            }

            /* CORREÇÃO DO TEXTO DO BOTÃO NO HOVER */
            [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover p {
                color: #0d1b2a !important;
            }
        </style>
    """, unsafe_allow_html=True)


def cabecalho(titulo, subtitulo=""):
    """
    Gera um bloco de titulo estilizado para o topo das paginas centrais.
    """
    st.markdown(f"""
        <div style="
            background: #1b3a5c; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 25px;
            border-left: 5px solid #00b4d8;
        ">
            <h2 style="color: white; margin: 0; padding: 0;">{titulo}</h2>
            {f'<p style="color: #a5f3fc; margin: 5px 0 0 0; font-size: 14px;">{subtitulo}</p>' if subtitulo else ''}
        </div>
    """, unsafe_allow_html=True)

def renderizar_card(titulo, descricao, cor_borda="#00b4d8", footer="", acao=None):
    st.markdown(f"""
    <div style="
        background: #ffffff; border: 1px solid #e2e8f0; 
        border-left: 4px solid {cor_borda}; border-radius: 8px; 
        padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ">
        <strong style="color: #1b3a5c; font-size: 16px;">{titulo}</strong>
        <p style="color: #4a5568; font-size: 14px; margin-top: 8px; margin-bottom: 0px;">{descricao}</p>
        <div style="margin-top: 10px; font-size: 12px; color: #718096;">{footer}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if acao:
        acao()

def formatar_titulo_aba(titulo):
    """Padroniza títulos de abas e seções."""
    st.markdown(f"### 🎯 {titulo}")

def formatar_legenda_instrucao(texto):
    """Padroniza textos explicativos curtos."""
    st.markdown(f"<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>{texto}</p>", unsafe_allow_html=True)

def container_alerta_padrao(titulo, mensagem):
    """Padroniza containers de aviso/diretrizes."""
    st.markdown(f"""
    <div style="background:#f8fafc; padding:15px; border-radius:8px; border-left: 4px solid #3b82f6; margin-bottom: 20px;">
        <strong style="color:#1e293b;">{titulo}</strong>
        <p style="margin: 5px 0 0 0; color:#475569; font-size: 14px;">{mensagem}</p>
    </div>
    """, unsafe_allow_html=True)