import streamlit as st
import time
from database.conexao import supabase
from services.batalha_service import (
    obter_estado_batalha, obter_pergunta_atual, obter_time_do_usuario, 
    obter_total_questoes, calcular_placar_atual, obter_nomes_dos_times,
    processar_resposta_assincrona, encerrar_partida_sincrona
)
from utils.estilo import aplicar_estilo

@st.fragment(run_every=3) # Atualiza o placar sozinho a cada 3 segundos
def placar_professor_tempo_real(b_id, ta_id, tb_id, nome_ta, nome_tb):
    # Consulta os pontos atualizados direto do banco
    pa, pb = calcular_placar_atual(b_id, ta_id, tb_id)
    
    # Desenha as métricas
    c1, c2 = st.columns(2)
    with c1:
        st.metric(f"Equipe: {nome_ta or 'Time A'}", f"{pa} Acertos")
    with c2:
        st.metric(f"Equipe: {nome_tb or 'Time B'}", f"{pb} Acertos")

def tela_batalha_rodada_assincrona():
    aplicar_estilo()
    
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id:
        st.error("Nenhuma arena selecionada.")
        if st.button("Voltar"): st.session_state.pagina = "batalha_de_equipes"; st.rerun()
        return

    b = obter_estado_batalha(b_id)
    if not b: st.error("Erro ao carregar arena."); return
    
    u = st.session_state.get("usuario_logado", {})
    tipo_u = str(u.get("tipo_usuario", "aluno")).lower()
    
    ta_id, tb_id = str(b.get("time_a_id", "")).strip(), str(b.get("time_b_id", "")).strip()
    nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
    total_q = obter_total_questoes(b_id)
    
    st.markdown(f"## ⏳ Missão Assíncrona: {b.get('titulo')}")

 # --- VISÃO DO PROFESSOR (DASHBOARD) ---
    if tipo_u in ("professor", "admin"):
        st.info("Você está na visão de governança. Alunos respondem no próprio ritmo.")
        
        # Chama o componente que se auto-atualiza
        placar_professor_tempo_real(b_id, ta_id, tb_id, nome_ta, nome_tb)
            
        st.divider()
        if st.button("🛑 Encerrar Batalha para Todos", type="primary"):
            encerrar_partida_sincrona(b_id)
            st.session_state.pagina = "batalha_resultado"
            st.rerun()

    # --- VISÃO DO ALUNO (PROGRESSÃO) ---
    else:
        times_usuario = obter_time_do_usuario(u.get("id"))
        tid = times_usuario[0] if times_usuario else None
        
        if not tid or (tid != ta_id and tid != tb_id):
            st.error("Você não pertence a nenhuma das equipes (A ou B) desta arena.")
            st.stop()

        # Calcula o progresso da equipe lendo as respostas já enviadas no banco
        respostas_equipe = supabase.table("batalha_respostas").select("id").eq("batalha_id", b_id).eq("time_id", tid).execute()
        respondidas = len(respostas_equipe.data) if respostas_equipe.data else 0
        ordem_atual = respondidas + 1

        # Barra de Progresso
        progresso = min(respondidas / total_q if total_q > 0 else 0, 1.0)
        st.progress(progresso, text=f"Progresso da sua equipe: {respondidas}/{total_q} questões concluídas")

        if ordem_atual > total_q:
            st.success("🎉 Sua equipe concluiu todas as missões desta arena!")
            st.info("Aguarde o professor encerrar a arena para revelar o placar final.")
            st.balloons()
        else:
            dados_p = obter_pergunta_atual(b_id, ordem_atual)
            if not dados_p:
                st.warning("Questão não encontrada. Contate o professor.")
            else:
                with st.container(border=True):
                    st.markdown(f"### 📍 Questão {ordem_atual}")
                    st.write(dados_p.get("enunciado"))
                    st.write("---")
                    
                    for alt in dados_p.get("alternativas", []):
                        if st.button(alt["texto"], key=f"alt_{alt['id']}", use_container_width=True):
                            resultado = processar_resposta_assincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"])
                            
                            if resultado == "acertou":
                                st.success("✅ Resposta Correta! Ponto para a equipe.")
                            elif resultado == "errou":
                                st.error("❌ Resposta Incorreta. Não houve pontuação nesta questão.")
                            elif resultado == "ja_respondida":
                                st.warning("⚠️ Outro membro da sua equipe já respondeu esta questão!")
                            
                            time.sleep(2)
                            st.rerun()

    st.write("")
    if st.button("⬅️ Sair da Arena"): 
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()