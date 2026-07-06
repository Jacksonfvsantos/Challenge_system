import streamlit as st
import datetime
from database.conexao import supabase
from services.batalha_service import (
    encerrar_partida_sincrona, processar_resposta_sincrona, 
    obter_estado_batalha, obter_pergunta_atual, obter_time_do_usuario, 
    calcular_placar_atual, obter_nomes_dos_times, iniciar_partida_sincrona, 
    listar_times
)
from utils.estilo import aplicar_estilo

def tela_batalha_rodada():
    aplicar_estilo()
    
    # 1. Validação de ID da Batalha (Evita o erro UUID: None)
    b_id = st.session_state.get("batalha_ativa_id")
    if not b_id or str(b_id).strip() == "None":
        st.error("Batalha não selecionada ou ID inválido.")
        if st.button("Voltar"): 
            st.session_state.pagina = "batalha_de_equipes"
            st.rerun()
        return
        
    # 2. Carrega estado atual direto do banco (Sem cache/fragmento para evitar atrasos)
    b = obter_estado_batalha(b_id)
    if not b: 
        st.error("Erro ao carregar arena.")
        return
    
    u = st.session_state.get("usuario_logado", {})
    tipo_u = str(u.get("tipo_usuario", "aluno")).lower()

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
                supabase.table("batalhas").update({"pergunta_atual_ordem": ordem_atual + 1}).eq("id", b_id).execute()
                st.rerun()

    # --- FLUXO DA PARTIDA ---
    if b.get("status") == "em_andamento":
        
        # Busca o ID do time do usuário logado
        times_usuario = obter_time_do_usuario(u.get("id"))
        tid = times_usuario[0] if times_usuario else None
        
        ta_id = str(b.get("time_a_id", "")).strip()
        tb_id = str(b.get("time_b_id", "")).strip()
        nome_ta, nome_tb = obter_nomes_dos_times(ta_id, tb_id)
        pa, pb = calcular_placar_atual(b_id, ta_id, tb_id)
        
        st.markdown(f"**Placar:** {nome_ta or 'Time A'} ({pa}) vs {nome_tb or 'Time B'} ({pb})")
        
        # Renderização da pergunta atual baseada na ordem salva no banco
        ordem = int(b.get("pergunta_atual_ordem", 1))
        dados_p = obter_pergunta_atual(b_id, ordem)

        if not dados_p:
             st.info("Aguardando próxima questão ou processando fim de jogo...")
        else:
            st.markdown(f"### 📍 {dados_p.get('enunciado')}")
            
            # Validação segura da vez
            tid_limpo = str(tid or "").strip().lower()
            vez_limpo = str(b.get("time_da_vez_id") or "").strip().lower()
            
            eh_vez = (tid_limpo == vez_limpo)
            if tipo_u in ("professor", "admin"):
                eh_vez = False # Professores apenas observam
            
            # Renderiza as alternativas
            for alt in dados_p.get("alternativas", []):
                if st.button(alt["texto"], key=f"alt_{alt['id']}", disabled=not eh_vez, use_container_width=True):
                    
                    # Verificação de segurança final contra UUID nulo
                    if not tid or tid == "None":
                        st.error("Erro: Você não está vinculado a um time para responder.")
                        return

                    adv = tb_id if tid_limpo == ta_id.lower() else ta_id
                    tentativa = 2 if b.get("status_sincrono") == "rebate_ativo" else 1
                    
                    # Chama o serviço para salvar a resposta e atualizar a ordem no banco
                    resultado = processar_resposta_sincrona(b_id, dados_p["id"], tid, alt["id"], alt["correta"], adv, tentativa)
                    
                    # Força a atualização da interface no mesmo instante
                    st.rerun()
                    
    elif b.get("status") == "finalizada":
        st.session_state.pagina = "batalha_resultado"
        st.rerun()
    else:
        st.info("Aguardando início da partida pelo professor.")

    if st.button("⬅️ Sair da Arena"): 
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()