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

# 🎯 Sub-módulos: MINI PROVAS (Roteador Dinâmico e Telas Secundárias do Aluno)
try:
    from telas.tela_mini_provas_principal import tela_mini_provas
except ImportError as e:
    mensagem_erro_prova = str(e)
    def tela_mini_provas(err=mensagem_erro_prova): 
        st.warning(f"Módulo de mini provas indisponível. Erro: {err}")
try:
    from telas.mini_provas.pontuacao_mini_provas import tela_pontuacao_mini_provas
except ImportError:
    def tela_pontuacao_mini_provas(): st.warning("Tela de pontuação específica de mini provas em desenvolvimento.")

try:
    from telas.mini_provas.desempenho_mini_provas import tela_desempenho_mini_provas
except ImportError:
    def tela_desempenho_mini_provas(): st.warning("Tela de desempenho de mini provas em desenvolvimento.")

# Imports dinâmicos das sub-telas das mini provas para evitar reset no State Router
try:
    from telas.mini_provas.realizar_mini_prova import tela_realizar_mini_prova
except ImportError:
    def tela_realizar_mini_prova(): st.error("Tela 'realizar_mini_prova' não localizada.")

try:
    from telas.mini_provas.responder import tela_responder_mini_prova
except ImportError:
    def tela_responder_mini_prova(): st.error("Tela 'responder' não localizada.")

try:
    from telas.mini_provas.resultado_mini_prova import tela_resultado_mini_prova
except ImportError:
    def tela_resultado_mini_prova(): st.error("Tela 'resultado_mini_prova' não localizada.")

try:
    from telas.mini_provas.resultados_mini_provas import tela_resultados_mini_provas
except ImportError:
    def tela_resultados_mini_provas(): st.error("Tela 'resultados_mini_provas' não localizada.")

# 🎯 Painel de Gerenciamento do Professor (Mapeado para o arquivo real)
try:
    from telas.mini_provas.mini_provas_professor import tela_mini_provas_professor
except ImportError:
    def tela_mini_provas_professor(): st.error("Módulo de gerenciamento do professor não localizado.")

# Fallbacks das demais páginas administrativas secundárias
def tela_cadastro_perguntas(): pass
def tela_lista_perguntas(): pass

# Sub-módulos: Arena de Batalha de Equipes (Bate-Rebate Síncrono)
try:
    from telas.batalha_de_equipes.batalha_de_equipes import tela_batalha_de_equipes
    from telas.batalha_de_equipes.times              import tela_batalha_times
    from telas.batalha_de_equipes.integrantes         import tela_batalha_integrantes
    from telas.batalha_de_equipes.gerenciar_batalhas import tela_batalha_gerenciar
    from telas.batalha_de_equipes.rodada              import tela_batalha_rodada
except ImportError as e:
    mensagem_fixa = str(e)
    def tela_batalha_de_equipes(err=mensagem_fixa): 
        st.error(f"❌ Erro interno de importação: {err}")
        st.info("💡 Dica: Verifique se algum arquivo dentro de 'telas/batalha_de_equipes/' ainda está importando o antigo 'batalha_de_equipes_service'.")
        
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
# 🚀 ROTEADOR INTELIGENTE VIA QUERY STRING (QR CODE / LINKS DIRETOS)
# ----------------------------------------------------------------------------
query_params = st.query_params

if "sala" in query_params and "id" in query_params:
    tipo_sala = str(query_params["sala"]).strip().lower()
    sala_id = str(query_params["id"]).strip()
    
    # Se o usuário não está logado, guarda a rota em cache de sessão para o pós-login
    if st.session_state.get("usuario_logado") is None:
        st.session_state["redirecionamento_pendente"] = {"sala": tipo_sala, "id": sala_id}
    else:
        # Usuário logado: Redireciona na hora para a tela correta da atividade
        if tipo_sala == "batalha":
            st.session_state.batalha_ativa_id = sala_id
            st.session_state.pagina = "batalha_rodada"
        elif tipo_sala == "quiz":
            st.session_state.quiz_ativo_id = sala_id
            st.session_state.pagina = "quiz_ao_vivo" 
        elif tipo_sala == "prova":
            st.session_state.prova_ativa_id = sala_id
            st.session_state.pagina = "mini_provas" 
            
        # Limpa os parâmetros da barra de endereços para liberar navegação livre
        st.query_params.clear()

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
# BARRA DE NAVEGAÇÃO LATERAL (Mantendo a Navbar funcional original externa)
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

# 🎯 Rotas do Módulo de Mini-Provas (Mapeamento Unificado e Seguro)
elif pagina == "mini_provas":
    tela_mini_provas()

elif pagina == "mini_provas_professor":
    tela_mini_provas_professor()

elif pagina == "pontuacao_mini_provas":
    tela_pontuacao_mini_provas()

elif pagina == "realizar_mini_prova":
    tela_realizar_mini_prova()

elif pagina == "prova_responder":
    tela_responder_mini_prova()

elif pagina == "resultados_mini_provas":
    tela_resultados_mini_provas()

elif pagina == "resultado_mini_prova":
    tela_resultado_mini_prova()

elif pagina == "cadastro_perguntas":
    tela_cadastro_perguntas()

elif pagina == "lista_perguntas":
    tela_lista_perguntas()

elif pagina == "desempenho_mini_provas":
    tela_desempenho_mini_provas()

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
    st.session_state.pagina = "home"
    st.rerun()