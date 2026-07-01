import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho, formatar_titulo_aba
from services.batalha_service import (
    listar_batalhas_ativas, deletar_batalha, iniciar_partida_sincrona, 
    encerrar_partida_sincrona, listar_times, cadastrar_nova_batalha, cadastrar_questao_rapida
)
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia

def tela_gerenciar_batalhas():
    aplicar_estilo()
  
    if st.button("⬅️ Voltar ao Painel"):
        st.session_state.pagina = "dashboard_professor"
        st.rerun()
    
    cabecalho("Gestão de Batalhas", "Administração de editais e monitoramento síncrono")

    aba_ativas, aba_nova = st.tabs(["🔥 Monitoramento", "✨ Criar Edital"])

    with aba_ativas:
        formatar_titulo_aba("Monitoramento de Batalhas")
        lista_ativas = listar_batalhas_ativas()

        if not lista_ativas:
            st.info("Nenhuma batalha encontrada.")
        else:
            for b in lista_ativas:
                with st.container(border=True):
                    st.markdown(f"**{b['titulo']}** | Status: {b.get('status', 'N/A')}")
                    col1, col2, col3 = st.columns(3)
                    
                    if b.get('status') == 'agendada':
                        if col1.button("▶️ Iniciar", key=f"start_{b['id']}"):
                            iniciar_partida_sincrona(b['id'], b.get('time_a_id'))
                            st.rerun()
                    elif b.get('status') == 'em_andamento':
                        if col2.button("⏹️ Encerrar", key=f"end_{b['id']}"):
                            encerrar_partida_sincrona(b['id'])
                            st.rerun()
                    
                    if col3.button("🗑️ Deletar", key=f"del_{b['id']}"):
                        deletar_batalha(b['id'])
                        st.rerun()

    with aba_nova:
        formatar_titulo_aba("1. Abrir Novo Edital")
        with st.form("form_nova_batalha"):
            titulo = st.text_input("Título da Batalha")
            descricao = st.text_area("Descrição / Regras")
            modalidade = st.selectbox("Modalidade:", ["sincrona", "assincrona"])
            times = listar_times()
            time_a = st.selectbox("Time A (Inicial):", options=[t['nome'] for t in times])
            time_b = st.selectbox("Time B (Adversário):", options=[t['nome'] for t in times])
            
            if st.form_submit_button("Criar Batalha"):
                t_a_id = next(t['id'] for t in times if t['nome'] == time_a)
                t_b_id = next(t['id'] for t in times if t['nome'] == time_b)
                res = cadastrar_nova_batalha(titulo, descricao, t_a_id, t_b_id, modalidade)
                if res["sucesso"]:
                    st.success("Batalha criada! Selecione-a abaixo para vincular questões.")
                else:
                    st.error(res["mensagem"])

        st.divider()
        formatar_titulo_aba("2. Adicionar Questões")
        lista_ativas_cadastro = listar_batalhas_ativas()
        
        if lista_ativas_cadastro:
            batalha_selecionada = st.selectbox("Vincular à batalha:", options=lista_ativas_cadastro, format_func=lambda x: x['titulo'])
            b_id = batalha_selecionada['id']
            
            metodo = st.radio("Método de cadastro:", ["Manual", "IA (PDF/DOCX)"])
            
            if metodo == "Manual":
                with st.form("form_manual"):
                    enunciado = st.text_area("Enunciado")
                    c1, c2 = st.columns(2)
                    alt = [c1.text_input("Alt A"), c2.text_input("Alt B"), c1.text_input("Alt C"), c2.text_input("Alt D")]
                    correta = st.selectbox("Correta (0=A, 1=B, 2=C, 3=D)", [0, 1, 2, 3])
                    if st.form_submit_button("Salvar Questão"):
                        cadastrar_questao_rapida(b_id, enunciado, alt, correta)
                        st.success("Questão salva!")
            
            else: # IA
                api_key = st.text_input("Gemini API Key", type="password")
                arquivo = st.file_uploader("Documento (PDF/DOCX)", type=["pdf", "docx"])
                if arquivo and api_key and st.button("Processar com IA"):
                    with st.spinner("Analisando arquivo..."):
                        extensao = arquivo.name.split('.')[-1]
                        texto = extrair_texto_de_arquivo(arquivo.getvalue(), extensao)
                        questoes = gerar_questoes_ia(texto, "Extraia questões técnicas.", api_key)
                        for q in questoes:
                            cadastrar_questao_rapida(b_id, q['enunciado'], q['alternativas'], q['correta_idx'])
                        st.success(f"{len(questoes)} questões vinculadas!")