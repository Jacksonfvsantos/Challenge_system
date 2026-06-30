import streamlit as st
import datetime
from database.conexao import supabase
from utils.estilo import aplicar_estilo, cabecalho
from services.ia_processador_service import extrair_texto_de_arquivo, gerar_questoes_ia
from services.mini_prova_service import (
    criar_escopo_mini_prova, 
    listar_provas_professor, 
    deletar_mini_prova, 
    salvar_questao_com_alternativas, 
    salvar_questoes_lote_ia
)

def tela_mini_provas_professor():
    aplicar_estilo()
    usuario = st.session_state.get("usuario_logado", {})
    usuario_id = usuario.get("id")
    
    cabecalho("Painel Docente", "Gestão de Mini Provas")

    if not usuario_id:
        st.error("Sessão inválida.")
        return

    aba_escopo, aba_manual, aba_importacao = st.tabs(["📝 1. Configurar Escopo", "✍️ 2. Cadastro Manual", "🤖 3. Importação IA"])

    with aba_escopo:
        with st.form("form_escopo", clear_on_submit=True):
            titulo = st.text_input("Título da Prova")
            disciplina = st.text_input("Disciplina")
            duracao = st.number_input("Duração (min)", value=30)
            xp = st.number_input("Pontuação XP", value=100)
            data_expiracao = st.date_input("Disponível até", datetime.date.today())
            instrucoes = st.text_area("Instruções")
            if st.form_submit_button("🚀 Criar Prova"):
                res = criar_escopo_mini_prova(titulo, duracao, usuario_id, data_expiracao.isoformat(), disciplina, xp, instrucoes)
                if res["sucesso"]: st.rerun()
                else: st.error(res["mensagem"])

    st.divider()
    st.subheader("🗑️ Provas Cadastradas")
    provas = listar_provas_professor(usuario_id)
    
    if not provas:
        st.info("Nenhuma prova criada.")
    else:
        for p in provas:
            col1, col2 = st.columns([5, 1])
            col1.write(f"**{p['titulo']}**")
            if col2.button("🗑️", key=f"del_{p['id']}"):
                res = deletar_mini_prova(p['id'])
                if res["sucesso"]: st.rerun()
                else: st.error("Erro ao deletar.")

        if provas:
            prova_id = st.selectbox("Selecione a prova para vincular:", options=[p['id'] for p in provas], format_func=lambda x: next(p['titulo'] for p in provas if p['id'] == x))
            
            with aba_manual:
                with st.form("manual"):
                    enunciado = st.text_area("Enunciado")
                    a, b, c, d = st.text_input("Alternativa A"), st.text_input("Alternativa B"), st.text_input("Alternativa C"), st.text_input("Alternativa D")
                    correta = st.selectbox("Correta", ["A", "B", "C", "D"])
                    if st.form_submit_button("Salvar Questão"):
                        salvar_questao_com_alternativas(prova_id, enunciado, [a, b, c, d], correta)
                        st.success("Questão salva!")

            with aba_importacao:
                arquivo = st.file_uploader("Upload de Caderno (PDF/DOCX)", type=["pdf", "docx"])
                prompt_custom = st.text_input("Instruções adicionais para a IA (opcional):", "Extraia questões de múltipla escolha com 4 alternativas.")
                
                if arquivo and st.button("🤖 Processar e Injetar Questões"):
                    with st.spinner("Processando arquivo e gerando questões com IA..."):
                        extensao = arquivo.name.split('.')[-1]
                        texto = extrair_texto_de_arquivo(arquivo.getvalue(), extensao)
    
                        questoes = gerar_questoes_ia(
                            texto_base=texto, 
                            prompt_adicional=prompt_custom, 
                            api_key=st.secrets["GEMINI_API_KEY"]
                        )
                        
                        if questoes:
                            res = salvar_questoes_lote_ia(prova_id, questoes)
                            if res["sucesso"]:
                                st.success(f"Sucesso! {res['mensagem']}")
                                st.rerun()
                            else:
                                st.error(res["mensagem"])
                        else:
                            st.warning("A IA não conseguiu extrair questões válidas do documento.")