import streamlit as st
import datetime
from utils.estilo import aplicar_estilo, cabecalho
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia
from services.mini_prova_service import (
    criar_escopo_mini_prova, 
    listar_provas_professor,
    salvar_questao_com_alternativas, 
    salvar_questoes_lote_ia,
    deletar_mini_prova
)

def tela_mini_provas_professor():
    aplicar_estilo()
    
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    
    cabecalho("Painel do Docente: Gestão de Mini Provas", "Cadastre novos exames e gerencie avaliações")

    if not usuario_id:
        st.error("Sessão de usuário inválida ou expirada.")
        return

    with st.expander("📝 Criar Nova Mini Prova", expanded=True):
        with st.form("form_cadastro_mini_prova", clear_on_submit=True):
            titulo = st.text_input("Título da Mini Prova:")
            disciplina = st.text_input("Componente Curricular:")
            
            col1, col2 = st.columns(2)
            duracao = col1.number_input("Duração (Minutos):", min_value=1, value=30)
            xp = col2.number_input("Pontuação (XP):", min_value=0, value=100)
            
            data_limite = st.date_input("Disponível até:", datetime.date.today())
            instrucoes = st.text_area("Instruções Adicionais:")
            
            if st.form_submit_button("🚀 Criar Definição da Prova"):
                res = criar_escopo_mini_prova(
                    titulo=titulo, 
                    duracao=duracao, 
                    usuario_id=usuario_id, 
                    data_limite=data_limite.isoformat(),
                    disciplina=disciplina,
                    xp=xp,
                    instrucoes=instrucoes
                )
                if res["sucesso"]:
                    st.success("Mini Prova registrada com sucesso!")
                    st.rerun()
                else:
                    st.error(res["mensagem"])

    st.subheader("🗑️ Provas Cadastradas")
    lista_provas = listar_provas_professor(usuario_id)
    
    if not lista_provas:
        st.info("Nenhuma prova criada no momento.")
    else:
        for prova in lista_provas:
            col_nome, col_del = st.columns([5, 1])
            col_nome.write(f"**{prova['titulo']}**")
            if col_del.button("🗑️", key=f"del_{prova['id']}"):
                res_del = deletar_mini_prova(prova['id'])
                if res_del["sucesso"]:
                    st.rerun()
                else:
                    st.error(f"Erro ao deletar: {res_del.get('mensagem', 'Falha desconhecida')}")

    if lista_provas:
        st.divider()
        dict_provas = {p["titulo"]: p["id"] for p in lista_provas}
        prova_selecionada = st.selectbox("Selecione a prova para gerir questões:", list(dict_provas.keys()))
        prova_id = dict_provas[prova_selecionada]

        aba_manual, aba_importacao = st.tabs(["✍️ Cadastro Manual", "🤖 Importação IA"])

        with aba_manual:
            with st.form("form_manual", clear_on_submit=True):
                enunciado = st.text_area("Enunciado:")
                alt_a = st.text_input("Alternativa A:")
                alt_b = st.text_input("Alternativa B:")
                alt_c = st.text_input("Alternativa C:")
                alt_d = st.text_input("Alternativa D:")
                correta = st.selectbox("Alternativa Correta:", ["A", "B", "C", "D"])
                
                if st.form_submit_button("📥 Gravar Questão"):
                    res = salvar_questao_com_alternativas(prova_id, enunciado, [alt_a, alt_b, alt_c, alt_d], correta)
                    if res["sucesso"]:
                        st.success(res["mensagem"])
                    else:
                        st.error(res["mensagem"])

        with aba_importacao:
            arquivo = st.file_uploader("Upload de Caderno:", type=["pdf", "docx"])
            prompt = st.text_input("Instruções para a IA:")
            
            if arquivo and st.button("🤖 Processar e Injetar Questões"):
                with st.spinner("IA processando..."):
                    texto = extrair_texto_de_arquivo(arquivo.getvalue(), arquivo.name.split('.')[-1])
                    questoes = gerar_questoes_ia(texto, prompt, st.secrets.get("GEMINI_API_KEY"))
                    res = salvar_questoes_lote_ia(prova_id, questoes)
                    if res["sucesso"]:
                        st.success(res["mensagem"])
                        st.rerun()
                    else:
                        st.error(res["mensagem"])

    if st.button("⬅️ Voltar ao Painel", use_container_width=True):
        st.session_state.pagina = "mini_provas"
        st.rerun()