import streamlit as st
import datetime
import time
from database.conexao import supabase
from services.batalha_service import (
    encerrar_partida_sincrona, processar_resposta_sincrona, 
    obter_estado_batalha, obter_pergunta_atual, obter_time_do_usuario, 
    calcular_placar_atual, obter_nomes_dos_times, processar_passagem_de_vez, 
    obter_total_questoes, iniciar_partida_sincrona, listar_times
)
from utils.estilo import aplicar_estilo

@st.fragment(run_every=1)
def motor_de_sincronia_unificado(b_id, eh_vez, tipo_u):
    try:
        b = obter_estado_batalha(b_id)
        if not b: return
        estado_composto = f"{b.get('pergunta_atual_ordem')}_{b.get('status')}_{b.get('status_sincrono')}"
        if "estado_local" not in st.session_state: st.session_state.estado_local = estado_composto
        
        # Se o estado mudou no banco, força a atualização da tela
        if st.session_state.estado_local != estado_composto:
            st.session_state.estado_local = estado_composto
            st.rerun()

        if b.get("status") == "em_andamento":
            agora = datetime.datetime.now(datetime.timezone.utc)
            inicio_turno_str = b.get("inicio_turno")
            
            # Proteção caso o turno não tenha sido registrado
            if not inicio_turno_str: inicio_turno_str = agora.isoformat()
            
            # Lida com o formato de data do Supabase
            inicio_dt = datetime.datetime.fromisoformat(str(inicio_turno_str).replace('Z', '+00:00'))
            
            tempo_passado = (agora - inicio_dt).total_seconds()
            tempo_limite = int(b.get("tempo_por_rodada", 45))
            tempo_restante = int(tempo_limite - tempo_passado)
            
            if tempo_restante <= 0:
                st.error("⏳ TEMPO ESGOTADO!")
                
                # Apenas o professor ou o aluno da vez mandam o comando pro banco para evitar duplicidade
                if eh_vez or tipo_u in ("professor", "admin"):
                    ta, tb = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
                    prox_time = tb if str(b.get("time_da_vez_id", "")).strip() == ta else ta
                    processar_passagem_de_vez(b_id, b.get("time_da_vez_id"), prox_time)
                
                time.sleep(1.5)
                st.rerun()
            else:
                st.metric("⏳ Tempo para responder", f"{max(0, tempo_restante)}s")
                
    except Exception as e:
        print(f"Erro no motor: {e}")

@st.fragment
def renderizador_pergunta(b_id, tid, ta_id, tb_id, tipo_u, status):
    b = obter_estado_batalha(b_id)
    ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, ordem)
    
    if not dados_p: 
        st.info("Aguardando próxima questão...")
        return

    st.markdown(f"### 📍 {dados_p.get('enunciado')}")
    
    # Tratamento de Strings para evitar erros de case/spaces
    tid_limpo = str(tid or "").strip().lower()
    vez_limpo = str(b.get("time_da_vez_id") or "").strip().lower()
    
    # Verifica se é o time do aluno que deve jogar agora
    eh_vez = (tid_limpo == vez_limpo)
    
    pode_clicar = False
    if tipo_u == "aluno" and eh_vez:
        pode_clicar = True

    st.write("---")
    
    # Renderização das Alternativas (Visíveis para todos, clicáveis apenas para o time da vez)
    for alt in dados_p.get("alternativas", []):
        if st.button(alt["texto"], key=f"alt_{alt['id']}", disabled=not pode_clicar, use_container_width=True):
            if not tid or tid == "None":
                st.error("Você não pertence a um time válido para responder.")
                st.stop()

            adv = tb_id if tid_limpo == ta_id.strip().lower() else ta_id
            tentativa = 2 if status == "rebate_ativo" else 1
            
            resultado = processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa)
            
            # --- FEEDBACKS VISUAIS GAMIFICADOS ---
            if isinstance(resultado, dict) and "erro" in resultado:
                st.error(f"⚠️ Erro: {resultado['erro']}")
                time.sleep(2)
            elif resultado == "acertou":
                st.success("🎉 RESPOSTA EXATA! Ponto garantido.")
                time.sleep(2)
            elif resultado == "rebate":
                st.warning("❌ INCORRETO! A equipe adversária ganhou a chance do REBATE!")
                time.sleep(2.5)
            elif resultado == "ambos_erraram":
                st.error("❌ INCORRETO NO REBATE! Nenhuma equipe pontuou. Avançando...")
                time.sleep(2)
            elif resultado == "fim_de_jogo":
                st.balloons()
                st.success("🏆 ÚLTIMA QUESTÃO CONCLUÍDA! Fim de jogo.")
                time.sleep(3)
            
            st.rerun()

def tela_batalha_rodada():
    aplicar_estilo()
    
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id or b_id == "None":
        st.error("Batalha não selecionada.")
        if st.button("Sair da Arena"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()
        return
        
    b = obter_estado_batalha(b_id)
    if not b: 
        st.error("Erro ao carregar arena.")
        return

    # Extrai as informações do usuário atual
    u = st.session_state.get("usuario_logado", {})
    tipo_u = str(u.get("tipo_usuario", "aluno")).lower()
    times_usuario = obter_time_do_usuario(u.get("id"))
    tid = times_usuario[0] if times_usuario else None
    
    # Verifica a vez (para enviar ao motor e renderizador)
    tid_limpo = str(tid or "").strip().lower()
    vez_limpo = str(b.get("time_da_vez_id") or "").strip().lower()
    eh_vez = (tid_limpo == vez_limpo)

    # Inicia o motor de sincronia de tempo
    motor_de_sincronia_unificado(b_id, eh_vez, tipo_u)

    # --- GOVERNANÇA DOCENTE ---
    if tipo_u in ("professor", "admin"):
        with st.expander("⚙️ Governança Docente", expanded=True):
            if b.get("status") == "agendada":
                times = listar_times()
                if times:
                    sel = st.selectbox("Quem iniciará a batalha?", options=[t['id'] for t in times], format_func=lambda x: next(t['nome'] for t in times if t['id'] == x))
                    if st.button("🚀 Iniciar Partida", type="primary"):
                        iniciar_partida_sincrona(b_id, sel)
                        st.rerun()
                        
            col1, col2 = st.columns(2)
            if col1.button("⏹️ Encerrar Partida"): 
                encerrar_partida_sincrona(b_id)
                st.session_state.pagina = "batalha_resultado"
                st.rerun()
                
            if col2.button("⏩ Pular Questão"): 
                ordem_atual = int(b.get("pergunta_atual_ordem", 1))
                total_q = obter_total_questoes(b_id)
                
                # Se o professor pular a última, finaliza o jogo automaticamente
                if ordem_atual >= total_q:
                    encerrar_partida_sincrona(b_id)
                else:
                    supabase.table("batalhas").update({"pergunta_atual_ordem": ordem_atual + 1}).eq("id", b_id).execute()
                st.rerun()

    # --- RENDERIZAÇÃO DA ARENA ---
    if b.get("status") == "em_andamento":
        ta_id, tb_id = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
        nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
        pa, pb = calcular_placar_atual(b_id, ta_id, tb_id)
        
        st.markdown(f"**Placar:** {nome_ta or 'Time A'} ({pa}) vs {nome_tb or 'Time B'} ({pb})")
        
        renderizador_pergunta(b_id, tid, ta_id, tb_id, tipo_u, b.get("status_sincrono"))
        
    elif b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()
        
    else:
        st.info("Aguardando início da partida pelo professor.")

    st.write("")
    if st.button("⬅️ Sair da Arena"): 
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()