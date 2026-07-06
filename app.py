import streamlit as st
import time
from utils.session import iniciar_session
from components.navbar import mostrar_menu

from telas.login import tela_login
from telas.cadastro import tela_cadastro
from telas.home import tela_home
from telas.quiz_rodada import tela_quiz_rodada
from telas.quiz_ranking_global import tela_quiz_ranking_global
from telas.cadastro_perguntas_quiz import tela_cadastro_perguntas_quiz
from telas.votacao import tela_votacao
from telas.regras import tela_central_regras
from telas.pontuacoes import tela_pontuacoes
from telas.desafios import tela_desafios
from telas.quiz_ao_vivo import tela_quiz_ao_vivo
from telas.recompensas import tela_recompensas
from telas.tela_mini_provas_principal import tela_mini_provas
from telas.mini_provas.pontuacao_mini_provas import tela_pontuacao_mini_provas
from telas.mini_provas.desempenho_mini_provas import tela_desempenho_mini_provas
from telas.mini_provas.historico_provas_professor import tela_historico_provas_professor
from telas.mini_provas.realizar_mini_prova import tela_realizar_mini_prova
from telas.mini_provas.responder import tela_responder_mini_prova
from telas.mini_provas.resultado_mini_prova import tela_resultado_mini_prova
from telas.mini_provas.resultados_mini_provas import tela_resultados_mini_provas
from telas.mini_provas.mini_provas_professor import tela_mini_provas_professor

def tela_batalha_de_equipes(): 
    try:
        from telas.batalha_de_equipes.batalha_de_equipes import tela_batalha_de_equipes as real_tela
        real_tela()
    except Exception as e: st.error(f"Erro ao carregar arena: {e}")

def tela_batalha_times(): 
    try:
        from telas.batalha_de_equipes.times import tela_batalha_times as real_tela
        real_tela()
    except Exception as e: st.error(f"Erro ao carregar times: {e}")

def tela_batalha_integrantes(): 
    try:
        from telas.batalha_de_equipes.integrantes import tela_batalha_integrantes as real_tela
        real_tela()
    except Exception as e: st.error(f"Erro ao carregar integrantes: {e}")

def tela_gerenciar_batalhas(): 
    try:
        from telas.batalha_de_equipes.gerenciar_batalhas import tela_gerenciar_batalhas as real_tela
        real_tela()
    except Exception as e: st.error(f"Erro ao carregar gestão: {e}")

def tela_batalha_rodada(): 
    try:
        from telas.batalha_de_equipes.rodada_sincrona import tela_batalha_rodada as real_tela
        real_tela()
    except Exception as e: st.error(f"Erro ao carregar rodada: {e}")

def tela_batalha_resultado(): 
    try:
        from telas.batalha_de_equipes.resultado_batalha_de_equipes import tela_batalha_resultado as real_tela
        real_tela()
    except Exception as e: st.error(f"Erro ao carregar resultado: {e}")

def tela_batalha_historico():
    try:
        from telas.batalha_de_equipes.historico import tela_historico_batalhas
        tela_historico_batalhas()
    except Exception as e: st.error(f"Erro ao carregar histórico: {e}")

def tela_batalha_rodada_assincrona(): 
    try:
        from telas.batalha_de_equipes.rodada_assincrona import tela_batalha_rodada_assincrona as real_tela
        real_tela()
    except Exception as e: st.error(f"Erro ao carregar rodada assíncrona: {e}")

st.set_page_config(page_title="Challenge System", layout="centered")
iniciar_session()

query_params = st.query_params
if "sala" in query_params and "id" in query_params:
    if not st.session_state.get("redirecionamento_processado"):
        st.session_state.batalha_ativa_id = str(query_params["id"]).strip()
        st.session_state.pagina = "batalha_rodada"
        st.session_state.redirecionamento_processado = True
        st.query_params.clear()
        st.rerun()

if not st.session_state.get("usuario_logado"):
    if st.session_state.get("pagina") == "cadastro":
        tela_cadastro()
    else:
        tela_login(None, 30)
    st.stop()

mostrar_menu(None)
pagina = st.session_state.get("pagina", "home")

rotas = {
    "home": tela_home,
    "desafios": tela_desafios,
    "votacao": tela_votacao,
    "pontuacoes": tela_pontuacoes,
    "regras_plataforma": tela_central_regras,
    "quiz_rodada": tela_quiz_rodada,
    "quiz_ranking_global": tela_quiz_ranking_global,
    "quiz_ao_vivo": tela_quiz_ao_vivo,
    "cadastro_perguntas_quiz": tela_cadastro_perguntas_quiz,
    "recompensas": tela_recompensas,
    "mini_provas": tela_mini_provas,
    "mini_provas_professor": tela_mini_provas_professor,
    "historico_provas_professor": tela_historico_provas_professor,
    "pontuacao_mini_provas": tela_pontuacao_mini_provas,
    "realizar_mini_prova": tela_realizar_mini_prova,
    "prova_responder": tela_responder_mini_prova,
    "resultados_mini_provas": tela_resultados_mini_provas,
    "resultado_mini_prova": tela_resultado_mini_prova,
    "desempenho_mini_provas": tela_desempenho_mini_provas,
    "batalha_de_equipes": tela_batalha_de_equipes,
    "batalha_times": tela_batalha_times,
    "batalha_integrantes": tela_batalha_integrantes,
    "batalha_gerenciar": tela_gerenciar_batalhas,
    "batalha_rodada": tela_batalha_rodada,
    "batalha_resultado": tela_batalha_resultado,
    "batalha_historico": tela_batalha_historico,
    "batalha_rodada_assincrona": tela_batalha_rodada_assincrona
}

if pagina in rotas:
    rotas[pagina]()
else:
    st.session_state.pagina = "home"
    st.rerun()