import streamlit as st
import datetime
from database.conexao import supabase
from services.batalha_service import (
    encerrar_partida_sincrona, processar_resposta_sincrona, 
    obter_estado_batalha, obter_pergunta_atual, obter_time_do_usuario, 
    calcular_placar_atual, obter_nomes_dos_times, processar_passagem_de_vez, 
    obter_total_questoes, iniciar_partida_sincrona, listar_times
)
from utils.estilo import aplicar_estilo

@st.fragment(run_every=1)
def motor_de_sincronia_unificado(b_id):
    try:
        b = obter_estado_batalha(b_id)
        if not b: return
        estado_composto = f"{b.get('pergunta_atual_ordem')}_{b.get('status')}_{b.get('status_sincrono')}"
        if "estado_local" not in st.session_state: st.session_state.estado_local = estado_composto
        if st.session_state.estado_local != estado_composto:
            st.session_state.estado_local = estado_composto
            st.rerun()

        if b.get("status") == "em_andamento":
            inicio = b.get("inicio_turno")
            if inicio:
                inicio_dt = datetime.datetime.fromisoformat(str(inicio).replace('Z', '+00:00'))
                tempo_passado = (datetime.datetime.now(datetime.timezone.utc) - inicio_dt).total_seconds()
                tempo_restante = 45 - int(tempo_passado)
                st.metric("⏳ Tempo para responder", f"{max(0, tempo_restante)}s")
                if tempo_restante <= 0:
                    ta, tb = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
                    prox_time = tb if str(b.get("time_da_vez_id", "")).strip() == ta else ta
                    processar_passagem_de_vez(b_id, b.get("time_da_vez_id"), prox_time)
                    st.rerun()
    except Exception as e:
        pass

# REMOVIDO o @st.fragment daqui para que o placar atualize junto com a resposta
def renderizador_pergunta(b_id, tid, ta_id, tb_id, tipo_u, status):
    b = obter_estado_batalha(b_id)
    ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, ordem)
    
    if not dados_p: 
        st.info("Aguardando próxima questão ou fim da partida...")
        return

    st.markdown(f"### 📍 {dados_p.get('enunciado')}")
    
    tid_limpo = str(tid or "").strip().lower()
    vez_limpo = str(b.get("time_da_vez_id") or "").strip().lower()
    
    eh_vez = (tid_limpo == vez_limpo)
    
    if tipo_u in ("professor", "admin"):
        eh_vez = False

    for alt in dados_p.get("alternativas", []):
        if st.button(alt["texto"], key=f"alt_{alt['id']}", disabled=not eh_vez, use_container_width=True):
            if not tid or tid == "None":
                st.error("Você não pertence a um time válido.")
                return

            adv = tb_id if tid_limpo == str(ta_id).strip().lower() else ta_id
            tentativa = 2 if status == "rebate_ativo" else 1
            
            resultado = processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa)
            
            if "erro" in resultado:
                st.error(resultado)
            else:
                st.toast(f"Resultado processado: {resultado}", icon="✅")
            
            st.rerun()

def tela_batalha_rodada():
    aplicar_estilo()
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id or b_id == "None":
        st.error("Batalha não selecionada.")
        if st.button("Voltar"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()
        return
        
    b = obter_estado_batalha(b_id)
    if not b: st.error("Erro ao carregar arena."); return
    
    motor_de_sincronia_unificado(b_id)

    if st.session_state.get("usuario_logado", {}).get("tipo_usuario") in ("professor", "admin"):
        with st.expander("⚙️ Governança Docente", expanded=True):
            if b.get("status") == "agendada":
                times = listar_times()
                # Exige que a arena tenha Equipe A e Equipe B definidas
                if times and len(times) >= 2:
                    t_a = st.selectbox("Selecione a Equipe A:", options=[t['id'] for t in times], format_func=lambda x: next(t['nome'] for t in times if t['id'] == x))
                    t_b = st.selectbox("Selecione a Equipe B:", options=[t['id'] for t in times], format_func=lambda x: next(t['nome'] for t in times if t['id'] == x))
                    sel = st.selectbox("Qual equipe começa respondendo?", options=[t_a, t_b], format_func=lambda x: next(t['nome'] for t in times if t['id'] == x))
                    
                    if st.button("🚀 Iniciar Partida", type="primary"):
                        if t_a == t_b:
                            st.error("As Equipes A e B devem ser diferentes!")
                        else:
                            # Preenche oficialmente as equipes na batalha
                            supabase.table("batalhas").update({"time_a_id": t_a, "time_b_id": t_b}).eq("id", b_id).execute()
                            iniciar_partida_sincrona(b_id, sel)
                            st.rerun()
                else:
                    st.warning("Cadastre pelo menos 2 equipes na aba anterior para iniciar.")
                    
            col1, col2 = st.columns(2)
            if col1.button("⏹️ Encerrar Partida"): encerrar_partida_sincrona(b_id); st.session_state.pagina = "batalha_resultado"; st.rerun()
            if col2.button("⏩ Pular Questão"): supabase.table("batalhas").update({"pergunta_atual_ordem": int(b.get("pergunta_atual_ordem", 1)) + 1}).eq("id", b_id).execute(); st.rerun()

    if b.get("status") == "em_andamento":
        u = st.session_state.get("usuario_logado", {})
        times_usuario = obter_time_do_usuario(u.get("id"))
        tid = times_usuario[0] if times_usuario else None
        
        ta_id, tb_id = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
        nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
        pa, pb = calcular_placar_atual(b_id, ta_id, tb_id)
        
        st.markdown(f"**Placar:** {nome_ta} ({pa}) vs {nome_tb} ({pb})")
        renderizador_pergunta(b_id, tid, ta_id, tb_id, str(u.get("tipo_usuario", "aluno")).lower(), b.get("status_sincrono"))
        
    elif b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"; st.rerun()
    else:
        st.info("Aguardando o professor configurar e iniciar a partida.")

    if st.button("⬅️ Sair da Arena"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()