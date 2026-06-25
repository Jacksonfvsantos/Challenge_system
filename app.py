import streamlit as st
import time
import datetime
import extra_streamlit_components as stx

from utils.session import iniciar_session
from components.navbar import mostrar_menu

# Imports de Telas Base Universais
from telas.login import tela_login
from telas.cadastro import tela_cadastro
from telas.home import tela_home
from telas.votacao import tela_votacao
from telas.regras import tela_central_regras
from telas.pontuacoes import tela_pontuacoes

# ----------------------------------------------------------------------------
# COMPONENTES ISOLADOS: IMPORTAÇÕES COM BLINDAGEM DE FALLBACK (TRY/EXCEPT)
# ----------------------------------------------------------------------------

try:
    from telas.desafios import tela_desafios
except ImportError:
    def tela_desafios(): st.warning("Tela de desafios em desenvolvimento.")

try:
    from telas.quiz_ao_vivo import tela_quiz_ao_vivo
except ImportError:
    def tela_quiz_ao_vivo(): st.warning("Tela de quiz ao vivo em desenvolvimento.")

try:
    from telas.recompensas import tela_recompensas
except ImportError:
    def tela_recompensas(): st.warning("Módulo de recompensas indisponível.")

# Sub-módulos: Mini Provas
try:
    from telas.mini_provas.mini_provas import tela_mini_provas
    from telas.mini_provas.mini_provas_professor import tela_mini_provas_professor
    from telas.mini_provas.cadastro_perguntas import tela_cadastro_perguntas
    from telas.mini_provas.lista_perguntas import tela_lista_perguntas
except ImportError:
    def tela_mini_provas(): st.warning("Módulo de mini provas indisponível.")
    def tela_mini_provas_professor(): pass
    def tela_cadastro_perguntas(): pass
    def tela_lista_perguntas(): pass

# Sub-módulos: Arena de Batalha de Equipes (Bate-Rebate Síncrono)
try:
    from telas.batalha_de_equipes.batalha_de_equipes import tela_batalha_de_equipes
    from telas.batalha_de_equipes.times              import tela_batalha_times
    from telas.batalha_de_equipes.integrantes         import tela_batalha_integrantes
    from telas.batalha_de_equipes.gerenciar_batalhas import tela_batalha_gerenciar
    from telas.batalha_de_equipes.rodada             import tela_batalha_rodada
except ImportError as e:
    # Captura a variável 'e' corretamente para evitar NameError
    def tela_batalha_de_equipes(): 
        st.error(f"Erro interno de importação: {e}")
    def tela_batalha_times(): pass
    def tela_batalha_integrantes(): pass
    def tela_batalha_gerenciar(): pass
    def tela_batalha_rodada(): pass

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO DE AMBIENTE E INICIALIZAÇÃO
# ----------------------------------------------------------------------------

st.set_page_config(
    page_title="Challenge System",
    layout="centered"
)

# Inicializa as variáveis padrões do st.session_state
iniciar_session()

# ----------------------------------------------------------------------------
# MECANISMO DE PERSISTÊNCIA DE SESSÃO (PROTEÇÃO CONTRA F5)
# ----------------------------------------------------------------------------

def obter_gerenciador_cookies():
    """Instancia o gerenciador de cookies diretamente sem travar o cache do Streamlit."""
    return stx.CookieManager()


cookie_manager = obter_gerenciador_cookies()

# Mantém o delay necessário para sincronia com o navegador do cliente
time.sleep(0.1)

# Definição do tempo limite de expiração da sessão ativa
MINUTOS_SESSAO_ATIVA = 30

# Se o session_state esvaziou pelo F5, tenta resgatar o usuário via cookie ativo
if not st.session_state.get("usuario_logado"):
    cookie_usuario = cookie_manager.get(cookie="user_session_token")
    
    if cookie_usuario and isinstance(cookie_usuario, dict):
        st.session_state.usuario_logado = cookie_usuario
        if "pagina" not in st.session_state:
            st.session_state.pagina = "home"
        st.rerun()

# ----------------------------------------------------------------------------
# CONTROLE DE FLUXO DE AUTENTICAÇÃO
# ----------------------------------------------------------------------------

if not st.session_state.get("usuario_logado"):
    pagina_auth = st.session_state.get("pagina", "login")
    if pagina_auth == "cadastro":
        tela_cadastro()
    else:
        tela_login(cookie_manager, MINUTOS_SESSAO_ATIVA)
    st.stop()

# ----------------------------------------------------------------------------
# BARRA DE NAVEGAÇÃO LATERAL (Injetando o cookie_manager para o Logout seguro)
# ----------------------------------------------------------------------------

mostrar_menu(cookie_manager)

# ----------------------------------------------------------------------------
# ROTEADOR DINÂMICO DE TELAS (STATE ROUTER)
# ----------------------------------------------------------------------------

pagina       = st.session_state.get("pagina", "home")
usuario      = st.session_state.get("usuario_logado", {})
tipo_usuario = str(usuario.get("tipo_usuario", "aluno")).lower()

if pagina == "home":
    tela_home()

elif pagina == "desafios":
    tela_desafios()

elif pagina == "votacao":
    tela_votacao()

elif pagina == "pontuacoes":
    tela_pontuacoes()

elif pagina == "regras_plataforma":
    tela_central_regras()

elif pagina == "quiz_ao_vivo":
    tela_quiz_ao_vivo()

elif pagina == "recompensas":
    tela_recompensas()

# Rotas do Módulo de Mini-Provas
elif pagina == "mini_provas":
    if tipo_usuario == "professor":
        tela_mini_provas_professor()
    else:
        tela_mini_provas()

elif pagina == "cadastro_perguntas":
    tela_cadastro_perguntas()

elif pagina == "lista_perguntas":
    tela_lista_perguntas()

# Rotas do Módulo de Batalhas de Equipe
elif pagina == "batalha_de_equipes":
    tela_batalha_de_equipes()

elif pagina == "batalha_times":
    tela_batalha_times()

elif pagina == "batalha_integrantes":
    tela_batalha_integrantes()

elif pagina == "batalha_gerenciar":
    tela_batalha_gerenciar()

elif pagina == "batalha_rodada":
    tela_batalha_rodada()

else:
    tela_home()