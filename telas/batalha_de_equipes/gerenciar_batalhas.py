import streamlit as st
from utils.estilo import aplicar_estilo, cabecalho, formatar_titulo_aba, formatar_legenda_instrucao
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

    aba_monitor, aba_escopo, aba_manual, aba_ia = st.tabs(["🔥 Monitoramento", "📝 Configurar Batalha", "✍️ Cadastro Manual", "🤖 Importação IA"])

    with aba_monitor:
        formatar_titulo_aba("Monitoramento de Batalhas")
        lista_ativas = listar_batalhas_ativas()
        if not lista_ativas:
            st.info("Nenhuma batalha encontrada.")
        else:
            for b in lista_ativas:
                with st.container(border=True):
                    st.markdown(f"**{b['titulo']}** | Status: {b.get('status', 'N/A')}")
                    c1, c2, c3 = st.columns(3)
                    if b.get('status') == 'agendada':
                        if c1.button("▶️ Iniciar", key=f"start_{b['id']}"): iniciar_partida_sincrona(b['id'], b.get('time_a_id')); st.rerun()
                    elif b.get('status') == 'em_andamento':
                        if c2.button("⏹️ Encerrar", key=f"end_{b['id']}"): encerrar_partida_sincrona(b['id']); st.rerun()
                    if c3.button("🗑️ Deletar", key=f"del_{b['id']}"): deletar_batalha(b['id']); st.rerun()

    with aba_escopo:
        formatar_titulo_aba("Abrir Nova Batalha")
        with st.form("form_nova_batalha", clear_on_submit=True):
            titulo = st.text_input("Título da Batalha")
            descricao = st.text_area("Descrição / Regras")
            modalidade = st.selectbox("Modalidade:", ["sincrona", "assincrona"])
            times = listar_times()
            time_a = st.selectbox("Time A (Inicial):", options=[t['nome'] for t in times])
            time_b = st.selectbox("Time B (Adversário):", options=[t['nome'] for t in times])
            if st.form_submit_button("Criar Edital"):
                t_a_id = next(t['id'] for t in times if t['nome'] == time_a)
                t_b_id = next(t['id'] for t in times if t['nome'] == time_b)
                res = cadastrar_nova_batalha(titulo, descricao, t_a_id, t_b_id, modalidade)
                if res["sucesso"]: st.success("Batalha criada com sucesso!"); st.rerun()
                else: st.error(res["mensagem"])

    lista_ativas = listar_batalhas_ativas()
    if lista_ativas:
        batalha_selecionada = st.selectbox("Selecione a batalha para vincular questões:", options=lista_ativas, format_func=lambda x: x['titulo'])
        b_id = batalha_selecionada['id']

        with aba_manual:
            with st.form("form_manual", clear_on_submit=True):
                enunciado = st.text_area("Enunciado da Questão")
                col1, col2 = st.columns(2)
                alt = [col1.text_input("A"), col2.text_input("B"), col1.text_input("C"), col2.text_input("D")]
                correta = st.selectbox("Alternativa Correta", ["A", "B", "C", "D"])
                if st.form_submit_button("Salvar Questão"):
                    cadastrar_questao_rapida(b_id, enunciado, alt, ["A", "B", "C", "D"].index(correta))
                    st.success("Questão cadastrada!")

        with aba_ia:
            formatar_legenda_instrucao("O upload de PDF/DOCX processará o documento via IA para gerar questões automaticamente.")
            arquivo = st.file_uploader("Documento de referência (PDF/DOCX)", type=["pdf", "docx"])
            prompt = st.text_input("Instruções adicionais para a IA:")
            if arquivo and st.button("🤖 Processar e Injetar Questões", type="primary"):
                with st.spinner("Analisando arquivo..."):
                    ext = arquivo.name.split('.')[-1]
                    texto = extrair_texto_de_arquivo(arquivo.getvalue(), ext)
                    questoes = gerar_questoes_ia(texto, prompt, st.secrets.get("GEMINI_API_KEY"))
                    for q in questoes:
                        cadastrar_questao_rapida(b_id, q['enunciado'], q['alternativas'], q['correta_idx'])
                    st.success(f"{len(questoes)} questões injetadas com sucesso!")
    else:
        aba_manual.info("Crie uma batalha na aba 'Configurar Batalha' primeiro.")
        aba_ia.info("Crie uma batalha na aba 'Configurar Batalha' primeiro.")