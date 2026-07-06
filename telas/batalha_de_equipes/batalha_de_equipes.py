import streamlit as st
import time
from utils.estilo import aplicar_estilo, cabecalho
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia
from services.batalha_service import (
    listar_batalhas_ativas, deletar_batalha, criar_time, listar_times,
    entrar_no_time, aluno_tem_time, listar_membros_time,
    remover_aluno, deletar_time, cadastrar_questao_rapida, 
    salvar_questoes_lote_ia, cadastrar_nova_batalha, 
    encerrar_partida_sincrona, obter_batalhas_finalizadas, iniciar_partida_sincrona
)

def tela_batalha_de_equipes():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = str(usuario.get("id", "")).strip()
    tipo_usuario = str(usuario.get("tipo_usuario") or usuario.get("tipo") or "aluno").lower()

    if st.button("⬅️ Voltar ao Dashboard"):
        st.session_state.pagina = "home"; st.rerun()
        
    cabecalho("⚔️ Arena de Batalha de Equipes", "Participe de desafios síncronos em tempo real")

    # --- GOVERNANÇA DOCENTE ---
    if tipo_usuario in ("professor", "admin"):
        with st.expander("👨‍🏫 Governança Docente"):
            st.subheader("⚙️ Nova Arena")
            with st.form("form_batalha"):
                titulo_b = st.text_input("Título da Arena:")
                modalidade = st.selectbox("Modalidade:", ["sincrona", "assincrona"])
                submit_arena = st.form_submit_button("Criar Arena")
            
            if submit_arena:
                if not titulo_b.strip():
                    st.error("⚠️ O título da arena é obrigatório!")
                else:
                    # Captura a resposta do serviço
                    resultado = cadastrar_nova_batalha(titulo_b, "Arena criada", None, None, modalidade)
                    
                    if resultado.get("sucesso"):
                        st.success("✅ Arena criada com sucesso!")
                        time.sleep(1) # Dá 1 segundo para você ler a mensagem de sucesso
                        st.rerun()    # Atualiza a tela para o card aparecer na lista
                    else:
                        st.error(f"❌ Erro ao criar arena: {resultado.get('mensagem')}")

            st.subheader("Gerenciar Equipes")
            for t in listar_times():
                with st.expander(f"Time: {t['nome']}"):
                    if st.button("Excluir Time", key=f"del_time_{t['id']}"):
                        deletar_time(t['id']); st.rerun()
                    for m in listar_membros_time(t['id']):
                        c1, c2 = st.columns([0.8, 0.2])
                        c1.write(f"- {m['nome']}")
                        if c2.button("Remover", key=f"rem_{m['id']}_{t['id']}"):
                            remover_aluno(t['id'], m['id']); st.rerun()
            
            st.divider()
            st.subheader("📝 Cadastrar Questão")
            
            # Inicializa fila se não existir
            if "questoes_pendentes" not in st.session_state: st.session_state.questoes_pendentes = []
            
            batalhas_disponiveis = listar_batalhas_ativas()
            
            # Trava de segurança: só exibe o formulário se houver arenas criadas
            if not batalhas_disponiveis:
                st.warning("⚠️ Nenhuma arena ativa encontrada. Crie uma nova arena acima para poder cadastrar questões.")
            else:
                b_sel = st.selectbox("Batalha destino:", batalhas_disponiveis, format_func=lambda x: x['titulo'])
                modo = st.radio("Método:", ["Manual", "Via IA"], horizontal=True)

                if modo == "Manual":
                    with st.form("form_manual"):
                        enun = st.text_area("Enunciado:")
                        a1, a2 = st.text_input("Alt A"), st.text_input("Alt B")
                        a3, a4 = st.text_input("Alt C"), st.text_input("Alt D")
                        correta = st.selectbox("Correta:", [0, 1, 2, 3], format_func=lambda x: f"Alt {x+1}")
                        
                        c1, c2 = st.columns(2)
                        btn_add = c1.form_submit_button("➕ Adicionar à Fila")
                        btn_salvar = c2.form_submit_button("✅ Salvar Fila no Banco")

                    if btn_add:
                        st.session_state.questoes_pendentes.append({
                            "enunciado": enun, "alternativas": [a1, a2, a3, a4], "correta_idx": correta
                        })
                        st.toast("Questão na fila!", icon="✅")
                    
                    if btn_salvar:
                        if st.session_state.questoes_pendentes:
                            res = salvar_questoes_lote_ia(b_sel['id'], st.session_state.questoes_pendentes)
                            if res["sucesso"]:
                                st.success(f"{len(st.session_state.questoes_pendentes)} questões cadastradas!")
                                st.session_state.questoes_pendentes = []
                                time.sleep(1); st.rerun()
                        else: st.warning("Fila vazia.")

                else:
                    prompt_custom = st.text_area("Instruções adicionais para a IA:", height=100)
                    arquivo = st.file_uploader("Upload de Caderno (PDF/DOCX)", type=["pdf", "docx"])
                    if arquivo and st.button("🤖 Processar e Injetar"):
                        with st.spinner("Processando..."):
                            texto = extrair_texto_de_arquivo(arquivo.getvalue(), arquivo.name.split('.')[-1])
                            questoes = gerar_questoes_ia(texto, prompt_custom, st.secrets["GEMINI_API_KEY"])
                            if questoes:
                                if salvar_questoes_lote_ia(b_sel['id'], questoes)["sucesso"]:
                                    st.balloons(); st.success("Questões importadas!"); st.rerun()

    # --- ARENA DE BATALHAS ---
    todas = listar_batalhas_ativas()
    historico = obter_batalhas_finalizadas()
    sinc, assinc, hist_s, hist_a = st.tabs(["⚡ Síncronas", "⏳ Assíncronas", "📜 Hist. Síncronas", "📜 Hist. Assíncronas"])
    with sinc: renderizar_lista([b for b in todas if b.get("modalidade") == "sincrona"])
    with assinc: renderizar_lista([b for b in todas if b.get("modalidade") == "assincrona"])
    with hist_s: renderizar_historico([h for h in historico if h.get("modalidade") == "sincrona"])
    with hist_a: renderizar_historico([h for h in historico if h.get("modalidade") == "assincrona"])

def renderizar_lista(lista):
    if not lista: st.info("Nenhuma batalha ativa."); return
    for ba in lista:
        with st.container(border=True):
            st.markdown(f"### {ba['titulo']}")
            if st.session_state.get("usuario_logado", {}).get("tipo_usuario") in ("professor", "admin"):
                c1, c2, c3 = st.columns(3)
                if c1.button("🚀 Iniciar", key=f"init_{ba['id']}"):
                    if iniciar_partida_sincrona(ba['id'], ba.get("time_a_id")): st.rerun()
                if c2.button("🛑 Encerrar", key=f"end_{ba['id']}"): encerrar_partida_sincrona(ba['id']); st.rerun()
                if c3.button("🗑️ Deletar", key=f"del_{ba['id']}"): deletar_batalha(ba['id']); st.rerun()
            if st.button(f"Entrar", key=f"entrar_{ba['id']}", use_container_width=True):
                st.session_state.batalha_ativa_id = ba["id"]; st.session_state.pagina = "batalha_rodada"; st.rerun()

def renderizar_historico(lista):
    for h in lista:
        with st.container(border=True): st.write(f"**{h['titulo']}** | {h['resultado_extenso']}")