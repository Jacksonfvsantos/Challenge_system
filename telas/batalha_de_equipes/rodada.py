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
    """Motor central estável para gerenciar estado e tempo."""
    try:
        b = obter_estado_batalha(b_id)
        if not b: return
        
        # Monitoramento robusto: só reroda se houver mudança real de estado
        estado_composto = f"{b.get('pergunta_atual_ordem')}_{b.get('status')}_{b.get('status_sincrono')}"
        if "estado_local" not in st.session_state: st.session_state.estado_local = estado_composto
        
        if st.session_state.estado_local != estado_composto:
            st.session_state.estado_local = estado_composto
            st.rerun()

        # Cronômetro integrado
        if b.get("status") == "em_andamento":
            inicio = b.get("inicio_turno")
            if inicio:
                inicio_dt = datetime.datetime.fromisoformat(str(inicio).replace('Z', '+00:00'))
                tempo_passado = (datetime.datetime.now(datetime.timezone.utc) - inicio_dt).total_seconds()
                tempo_restante = 45 - int(tempo_passado)
                
                st.metric("Tempo para responder", f"{max(0, tempo_restante)}s")
                
                if tempo_restante <= 0:
                    ta, tb = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
                    prox_time = tb if str(b.get("time_da_vez_id", "")).strip() == ta else ta
                    processar_passagem_de_vez(b_id, b.get("time_da_vez_id"), prox_time)
                    st.rerun()
    except Exception as e:
        print(f"Erro no motor unificado: {e}")

@st.fragment
def renderizador_pergunta(b_id, tid, ta_id, tb_id, tipo_u, status):
    b = obter_estado_batalha(b_id)
    ordem = int(b.get("pergunta_atual_ordem", 1))
    dados_p = obter_pergunta_atual(b_id, ordem)
    if not dados_p: st.info("Aguardando próxima questão..."); return

    st.markdown(f"### 📍 {dados_p.get('enunciado')}")
    
    tid_limpo = str(tid).strip().lower()
    vez_limpo = str(b.get("time_da_vez_id", "")).strip().lower()
    eh_vez = (tid_limpo == vez_limpo and tipo_u not in ("professor", "admin"))
    
    for alt in dados_p.get("alternativas", []):
        # DEBUG: Se o botão estiver desabilitado, você não saberá o porquê.
        # Vamos adicionar um tooltip ou verificar o estado lógico.
        eh_vez = (tid_limpo == vez_limpo and tipo_u not in ("professor", "admin"))
        
        # Se você clicar e não acontecer nada, o st.button retornará False.
        if st.button(alt["texto"], key=f"alt_{alt['id']}", disabled=not eh_vez, use_container_width=True):
            adv = tb_id if tid_limpo == ta_id.strip().lower() else ta_id
            tentativa = 2 if status == "rebate_ativo" else 1
            
            # Captura a resposta do serviço
            resultado = processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa)
            
            # Debug visual na tela
            st.warning(f"Resultado processado: {resultado}")
            
            # Força o rerun apenas após o processamento
            st.rerun()

def tela_batalha_rodada():
    aplicar_estilo()
    
    # Validação crítica para evitar erro de UUID None
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id or b_id == "None":
        st.error("Batalha não selecionada.")
        if st.button("Voltar"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()
        return
        
    b = obter_estado_batalha(b_id)
    if not b: st.error("Erro ao carregar dados da arena."); return
    
    motor_de_sincronia_unificado(b_id)

    # --- GOVERNANÇA DOCENTE ---
    if st.session_state.get("usuario_logado", {}).get("tipo_usuario") in ("professor", "admin"):
        with st.expander("⚙️ Governança Docente", expanded=True):
            if b.get("status") == "agendada":
                times = listar_times()
                if times:
                    sel = st.selectbox("Quem iniciará a batalha?", options=[t['id'] for t in times], format_func=lambda x: next(t['nome'] for t in times if t['id'] == x))
                    if st.button("🚀 Iniciar Partida", type="primary"):
                        iniciar_partida_sincrona(b_id, sel); st.rerun()
            
            col1, col2 = st.columns(2)
            if col1.button("⏹️ Encerrar Partida"): encerrar_partida_sincrona(b_id); st.session_state.pagina = "batalha_resultado"; st.rerun()
            if col2.button("⏩ Pular Questão"): supabase.table("batalhas").update({"pergunta_atual_ordem": int(b.get("pergunta_atual_ordem", 1)) + 1}).eq("id", b_id).execute(); st.rerun()

    # --- FLUXO DA PARTIDA ---
    if b.get("status") == "em_andamento":
        u = st.session_state.get("usuario_logado", {})
        tid = obter_time_do_usuario(u.get("id"))[0]
        ta_id, tb_id = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
        nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
        pa, pb = calcular_placar_atual(b_id, ta_id, tb_id)
        
        st.markdown(f"**Placar:** {nome_ta or 'Time A'} ({pa}) vs {nome_tb or 'Time B'} ({pb})")
        renderizador_pergunta(b_id, tid, ta_id, tb_id, str(u.get("tipo_usuario", "aluno")).lower(), b.get("status_sincrono"))
        
    elif b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"; st.rerun()
    else:
        st.info("Aguardando início da partida pelo professor.")

    if st.button("⬅️ Voltar"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()