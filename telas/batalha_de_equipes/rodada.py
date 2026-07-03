import streamlit as st
import time, datetime
from utils.estilo import aplicar_estilo, cabecalho
from database.conexao import supabase 
from services.batalha_service import (
    encerrar_partida_sincrona, processar_resposta_sincrona, 
    processar_resposta_assincrona, obter_estado_batalha, iniciar_partida_sincrona,
    obter_pergunta_atual, obter_time_do_usuario, calcular_placar_atual, obter_nomes_dos_times
)
from utils.estilo import aplicar_estilo

@st.fragment(run_every=2)
def painel_estatistico_reativo(batalha_id, time_a_id, time_b_id, nome_ta, nome_tb):
    pa, pb = calcular_placar_atual(batalha_id, time_a_id, time_b_id)
    st.markdown(f"**Placar:** {nome_ta} {pa} vs {nome_tb} {pb}", unsafe_allow_html=True)

@st.fragment(run_every=2)
def renderizador_pergunta_reativo(b_id, tid, ta_id, tb_id, tipo_u):
    b = obter_estado_batalha(b_id)
    p_ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, p_ordem)
    
    if not dados_p:
        st.info("⏳ Aguardando próxima questão ou fim da partida...")
        return

    st.markdown(f"### 📍 {dados_p['enunciado']}")
    
    tid_limpo = str(tid).strip().lower() if tid else "none"
    vez_limpo = str(b.get("time_da_vez_id", "")).strip().lower()
    
    eh_vez = (tid_limpo == vez_limpo)
    
    if tipo_u in ("professor", "admin"):
        eh_vez = False
        st.info("👁️ Modo Observador: Apenas times podem responder.")

    for alt in dados_p["alternativas"]:
        if st.button(alt["texto"], key=f"alt_{alt['id']}", use_container_width=True, disabled=not eh_vez):
            if b.get("modalidade") == "sincrona":
                tentativa = 2 if b.get("status_sincrono") == "rebate_ativo" else 1
                adversario_id = tb_id if tid_limpo == ta_id.strip().lower() else ta_id
                
                res = processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adversario_id, tentativa)
                st.toast(f"Resultado: {res}")
            else:
                processar_resposta_assincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"])
                st.success("Resposta registrada!")
            time.sleep(0.5); st.rerun()

@st.fragment(run_every=1)
def cronometro_reativo(b_id, time_da_vez, b):
    inicio = b.get("inicio_turno")
    if not inicio: return
    
    inicio_dt = datetime.datetime.fromisoformat(inicio.replace('Z', '+00:00'))
    tempo_passado = (datetime.datetime.now(datetime.timezone.utc) - inicio_dt).total_seconds()
    tempo_restante = 45 - int(tempo_passado)
    
    if tempo_restante <= 0:
        ordem_atual = int(b.get("pergunta_atual_ordem", 1))
        novo_time = b.get("time_b_id") if time_da_vez == b.get("time_a_id") else b.get("time_a_id")
        
        pergunta = obter_pergunta_atual(b_id, ordem_atual)
        if pergunta:
            supabase.table("batalha_respostas").insert({
                "batalha_id": b_id,
                "questao_id": pergunta["id"],
                "time_id": time_da_vez,
                "resposta_correta": False,
                "tentativa_numero": 1
            }).execute()

        supabase.table("batalhas").update({
            "pergunta_atual_ordem": ordem_atual + 1,
            "time_da_vez_id": novo_time,
            "inicio_turno": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status_sincrono": "aguardando_resposta"
        }).eq("id", b_id).execute()
        
        st.toast("⏳ Tempo esgotado! Avançando para a próxima questão.")
        st.rerun()
    else:
        st.metric("Tempo para responder", f"{tempo_restante}s")

def tela_batalha_rodada():
    aplicar_estilo()
    
    b_id = st.session_state.get("batalha_ativa_id")
    b = obter_estado_batalha(b_id)

    if not b or b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()

    u = st.session_state.get("usuario_logado", {})
    tipo_u = str(u.get("tipo_usuario", "aluno")).lower()
    uid = u.get("id")
    tid = obter_time_do_usuario(uid)[0]
    
    ta_id, tb_id = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
    nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)

    if st.button("⬅️ Voltar para a Arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    painel_estatistico_reativo(b_id, ta_id, tb_id, nome_ta, nome_tb)
    
    if b.get("status") == "em_andamento":
        cronometro_reativo(b_id, b.get("time_da_vez_id"), b)
        renderizador_pergunta_reativo(b_id, tid, ta_id, tb_id, tipo_u)
    else:
        st.info("A partida ainda não começou.")

    if tipo_u in ("professor", "admin"):
        with st.expander("⚙️ Painel de Governança Docente"):
            if b.get("status") == "agendada" and st.button("🔥 Iniciar Partida Agora"):
                iniciar_partida_sincrona(b_id, ta_id)
                st.rerun()
            
            if st.button("⏹️ Encerrar Partida Agora", type="primary"):
                if encerrar_partida_sincrona(b_id):
                    st.session_state.pagina = "batalha_resultado"
                    st.rerun()

def tela_batalha_resultado():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    
    res = supabase.table("historico_batalhas").select("*").eq("batalha_id", b_id).execute()
    
    if res.data:
        info = res.data[0]
        st.balloons()
        cabecalho("🏁 Partida Encerrada!", "Resultado final da batalha")
        
        with st.container(border=True):
            st.markdown(f"### {info['resultado_extenso']}")
            st.write(f"**Pontuação:** {info['time_a_nome']}: {info['pontos_time_a']} | {info['time_b_nome']}: {info['pontos_time_b']}")
    
    if st.button("🏠 Voltar para a Arena"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()