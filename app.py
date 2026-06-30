import streamlit as st
import time
import datetime
import extra_streamlit_components as stx

from utils.session import iniciar_session
from components.navbar import mostrar_menu

from telas.quiz_rodada import tela_quiz_rodada
from telas.quiz_ranking_global import tela_quiz_ranking_global
from telas.cadastro_perguntas_quiz import tela_cadastro_perguntas_quiz
from telas.login import tela_login
from telas.cadastro import tela_cadastro
from telas.home import tela_home
from telas.votacao import tela_votacao
from telas.regras import tela_central_regras
from telas.pontuacoes import tela_pontuacoes

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

try:
    from telas.mini_provas.historico_provas_professor import tela_historico_provas_professor
except ImportError:
    def tela_historico_provas_professor(): st.error("Módulo de histórico do professor não localizado.")

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

try:
    from telas.mini_provas.mini_provas_professor import tela_mini_provas_professor
except ImportError:
    def tela_mini_provas_professor(): st.error("Módulo de gerenciamento do professor não localizado.")

def tela_cadastro_perguntas(): pass
def tela_lista_perguntas(): pass

try:
    from telas.batalha_de_equipes.batalha_de_equipes import tela_batalha_de_equipes
    from telas.batalha_de_equipes.times              import tela_batalha_times
    from telas.batalha_de_equipes.integrantes         import tela_batalha_integrantes
    from telas.batalha_de_equipes.gerenciar_batalhas import tela_batalha_de_equipes
    from telas.batalha_de_equipes.rodada              import tela_batalha_rodada
except ImportError as e:
    mensagem_fixa = str(e)
    def tela_batalha_de_equipes(err=mensagem_fixa): 
        st.error(f"❌ Erro interno de importação: {err}")
        
    def tela_batalha_times(): pass
    def tela_batalha_integrantes(): pass
    def tela_batalha_gerenciar(): pass
    def tela_batalha_rodada(): pass

st.set_page_config(
    page_title="Challenge System",
    layout="centered"
)

iniciar_session()

def obter_gerenciador_cookies():
    return stx.CookieManager()

cookie_manager = obter_gerenciador_cookies()
time.sleep(0.1)

MINUTOS_SESSAO_ATIVA = 30

if not st.session_state.get("usuario_logado"):
    cookie_usuario = cookie_manager.get(cookie="user_session_token")
    if cookie_usuario and isinstance(cookie_usuario, dict):
        st.session_state.usuario_logado = cookie_usuario
        if "pagina" not in st.session_state:
            st.session_state.pagina = "home"
        st.rerun()

query_params = st.query_params

if "sala" in query_params and "id" in query_params:
    tipo_sala = str(query_params["sala"]).strip().lower()
    sala_id = str(query_params["id"]).strip()
    
    if st.session_state.get("usuario_logado") is None:
        st.session_state["redirecionamento_pendente"] = {"sala": tipo_sala, "id": sala_id}
    else:
        if tipo_sala == "batalha":
            st.session_state.batalha_ativa_id = sala_id
            st.session_state.pagina = "batalha_rodada"
        elif tipo_sala == "quiz":
            st.session_state.quiz_ativo_id = sala_id
            st.session_state.pagina = "quiz_ao_vivo" 
        elif tipo_sala == "prova":
            st.session_state.prova_ativa_id = sala_id
            st.session_state.pagina = "mini_provas" 
            
        st.query_params.clear()

if not st.session_state.get("usuario_logado"):
    pagina_auth = st.session_state.get("pagina", "login")
    if pagina_auth == "cadastro":
        tela_cadastro()
    else:
        tela_login(cookie_manager, MINUTOS_SESSAO_ATIVA)
    st.stop()

mostrar_menu(cookie_manager)

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

elif pagina == "quiz_rodada":
    tela_quiz_rodada()

elif pagina == "quiz_ranking_global":
    tela_quiz_ranking_global()

elif pagina == "quiz_ao_vivo":
    tela_quiz_ao_vivo()

elif pagina == "cadastro_perguntas_quiz":
    tela_cadastro_perguntas_quiz()

elif pagina == "recompensas":
    tela_recompensas()

elif pagina == "mini_provas":
    tela_mini_provas()

elif pagina == "mini_provas_professor":
    tela_mini_provas_professor()

elif pagina == "historico_provas_professor":
    tela_historico_provas_professor()

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