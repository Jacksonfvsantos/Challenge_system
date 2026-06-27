import streamlit as st
import time
from database.conexao import supabase
from services.batalha_service import (
    encerrar_partida_sincrona, 
    processar_resposta_sincrona, 
    obter_estado_batalha,
    iniciar_partida_sincrona
)
from utils.estilo import aplicar_estilo 

def obter_nomes_dos_times(time_a_id, time_b_id):
    try:
        res = supabase.table("times").select("id, nome").in_("id", [time_a_id, time_b_id]).execute()
        mapeamento = {str(t["id"]).strip(): t["nome"] for t in res.data} if res.data else {}
        return mapeamento.get(str(time_a_id).strip(), "Time A"), mapeamento.get(str(time_b_id).strip(), "Time B")
    except Exception: 
        return "Time A", "Time B"

def obter_pergunta_atual(batalha_id, ordem_pergunta):
    try:
        vinculo = supabase.table("batalha_perguntas").select("questao_id").eq("batalha_id", batalha_id).eq("ordem", int(ordem_pergunta)).execute()
        if not vinculo.data: 
            return None
        q_id = str(vinculo.data[0]["questao_id"]).strip()
        dados_questao = supabase.table("questoes").select("*").eq("id", q_id).execute().data[0]
        alternativas = supabase.table("alternativas").select("*").eq("questao_id", q_id).order("ordem").execute().data or []
        
        return {
            "id": q_id, "enunciado": dados_questao.get("enunciado", "Sem enunciado"),
            "alternativas": [{"id": a["id"], "texto": a["texto"], "ordem": a["ordem"], "correta": bool(a.get("correta", False))} for a in alternativas]
        }
    except Exception: 
        return None

def obter_time_do_usuario(usuario_id):
    try:
        res = supabase.table("time_membros").select("time_id, times(nome)").eq("usuario_id", usuario_id).execute()
        return (str(res.data[0]["time_id"]).strip(), res.data[0]["times"]["nome"]) if res.data else (None, None)
    except Exception: 
        return None, None

def calcular_placar_atual(batalha_id, time_a_id, time_b_id):
    try:
        res = supabase.table("batalha_respostas").select("time_id, reply_correta").eq("batalha_id", batalha_id).execute()
        pa, pb = 0, 0
        if res.data:
            for r in res.data:
                if r.get("resposta_correta") is True:
                    if str(r.get("time_id")).strip() == str(time_a_id).strip(): 
                        pa += 1
                    elif str(r.get("time_id")).strip() == str(time_b_id).strip(): 
                        pb += 1
        return pa, pb
    except Exception: 
        return 0, 0

@st.fragment(run_every=3)
def painel_estatistico_reativo(batalha_id, time_a_id, time_b_id, nome_time_a, nome_time_b, dados_pergunta, ordem_at, status_at):
    bl = obter_estado_batalha(batalha_id)
    if bl and (int(bl.get("pergunta_atual_ordem", 1)) != int(ordem_at) or str(bl.get("status_sincrono")) != str(status_at)):
        st.session_state["forcar_refresh_global"] = True
        st.rerun()

    pa, pb = calcular_placar_atual(batalha_id, time_a_id, time_b_id)
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px; border: 1px solid #334155;">
        <span style="color: #38bdf8; font-size: 18px; font-weight: bold;">{nome_time_a}: {pa} XP</span> 
        <span style="color: #fb923c; font-size: 18px; font-weight: bold;"> vs {nome_time_b}: {pb} XP</span>
    </div>
    """, unsafe_allow_html=True)

def tela_quiz_rodada():
    aplicar_estilo()
    if st.session_state.get("forcar_refresh_global", False):
        st.session_state["forcar_refresh_global"] = False
        st.rerun()

    u = st.session_state.get("usuario_logado", {})
    uid = str(u.get("id", "")).strip()
    tipo = str(u.get("tipo_usuario", "aluno")).lower()
    
    if tipo == "aluno":
        tid, tnome = obter_time_do_usuario(uid)
        if not tid: 
            st.error("Você precisa de uma equipe!")
            return
    else: 
        tid, tnome = "PROFESSOR_CONSOLA", "Painel Docente"
    
    if "batalha_ativa_id" not in st.session_state: 
        return
    b_id = st.session_state.batalha_ativa_id
    b = obter_estado_batalha(b_id)
    
    if not b:
        st.warning("Batalha não localizada.")
        return

    ta_id, tb_id = str(b.get("time_a_id")).strip(), str(b.get("time_b_id")).strip()
    nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
    p_ordem = int(b.get("pergunta_atual_ordem", 1))
    st_sinc = str(b.get("status_sincrono", "aguardando_resposta"))
    dados_p = obter_pergunta_atual(b_id, p_ordem)

    painel_estatistico_reativo(b_id, ta_id, tb_id, nome_ta, nome_tb, dados_p, p_ordem, st_sinc)

    if b.get("finalizada") is True or str(b.get("status")).lower() == "finalizada" or not dados_p:
        if dados_p is None and not b.get("finalizada"):
            encerrar_partida_sincrona(b_id)
        st.success("🏁 **A batalha foi encerrada oficialmente!**")
        pa, pb = calcular_placar_atual(b_id, ta_id, tb_id)
        if pa > pb: 
            st.info(f"🥇 **Vencedor:** {nome_ta} ({pa} XP) | 🥈 {nome_tb} ({pb} XP)")
        elif pb > pa: 
            st.info(f"🥇 **Vencedor:** {nome_tb} ({pb} XP) | 🥈 {nome_ta} ({pa} XP)")
        else: 
            st.warning(f"🤝 **Resultado:** Empate técnico ({pa} XP)")
        
        if st.button("⬅️ Voltar para a Arena de Equipes", use_container_width=True):
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return

    if tipo in ("professor", "admin") and str(b.get("status")).lower() == "agendada":
        if st.button("🔥 Começar Partida Agora!", type="primary", use_container_width=True):
            iniciar_partida_sincrona(b_id, ta_id)
            st.rerun()
        return

    st.markdown(f"### 📍 Pergunta: {dados_p['enunciado']}")
    eh_vez = (str(tid).strip() == str(b.get("time_da_vez_id")).strip())
    tentativa = 2 if st_sinc == "rebate_ativo" else 1

    if tipo == "aluno" and str(tid) in (ta_id, tb_id):
        if eh_vez: 
            st.markdown(f"<div style='background-color: #065f46; padding: 12px; border-radius: 5px; color: white;'>🟢 SEU TIME RESPONDE AGORA! (Tentativa {tentativa}ª)</div>", unsafe_allow_html=True)
        else: 
            st.markdown("<div style='background-color: #7c2d12; padding: 12px; border-radius: 5px; color: white;'>⏱️ ADVERSÁRIO A RESPONDER...</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    for alt in dados_p["alternativas"]:
        letra = chr(64 + int(alt["ordem"]))
        if st.button(f"{letra}) {alt['texto']}", key=f"alt_{alt['id']}", use_container_width=True, disabled=not (eh_vez and tipo == "aluno")):
            processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], tb_id if str(tid) == ta_id else ta_id, tentativa)
            time.sleep(0.4)
            st.rerun()

    st.markdown("<br><hr>", unsafe_allow_html=True)
    if st.button("🚪 Sair da Sala de Aula", use_container_width=True, type="secondary"):
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()