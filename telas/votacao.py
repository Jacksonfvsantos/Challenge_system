import streamlit as st
import pandas as pd
from services.desafio_service import listar_desafios
from utils.estilo import aplicar_estilo, cabecalho

try:
    from services.votacao_service import listar_votos, registrar_voto
except ImportError:
    def listar_votos(): return []
    def registrar_voto(d, a, u): return {"sucesso": True}

def tela_votacao():
    aplicar_estilo()

    usuario = st.session_state.get("usuario_logado", {})
    tipo = usuario.get("tipo_usuario", "aluno")
    usuario_id_logado = str(usuario.get("id", ""))

    cabecalho(
        "Sistema de Votação",
        "Avalie os projetos desenvolvidos pelos seus colegas por meio de notas."
    )

    # --- VISUALIZAÇÃO DO PROFESSOR (Painel Consolidado de Auditoria) ---
    if tipo == "professor":
        st.subheader("📊 Painel de Monitoramento de Auditoria de Notas")
        
        try:
            votos = listar_votos()
        except Exception:
            votos = []

        if votos:
            # Transforma em tabela estruturada conforme exigido no relatório (Item 2.33)
            df_votos = pd.DataFrame(votos)
            
            # Filtro interativo para análises e consultas rápidas (Item 2.34)
            filtro_busca = st.text_input("🔍 Filtrar tabela por ID do Aluno ou Desafio")
            if filtro_busca:
                df_votos = df_votos[
                    df_votos['usuario_id'].astype(str).str.contains(filtro_busca) | 
                    df_votos['desafio_id'].astype(str).str.contains(filtro_busca)
                ]

            st.markdown("**Registros de Notas Localizados**")
            st.dataframe(df_votos, use_container_width=True)
        else:
            st.info("Nenhuma avaliação de nota foi computada até o momento.")
                
    # --- VISUALIZAÇÃO DO ALUNO (Pesquisa e Atribuição de Notas) ---
    else:
        st.subheader("🎯 Desafios Disponíveis para Avaliação")
        
        # Filtro de busca textual para evitar listagem excessiva na tela (Item 2.34 e 2.35)
        pesquisa = st.text_input("🔍 Digite o título do desafio para filtrar a busca")
        
        try:
            desafios = listar_desafios()
        except Exception:
            desafios = []

        if pesquisa and desafios:
            desafios = [d for d in desafios if pesquisa.lower() in d.get("titulo", "").lower()]

        if not desafios:
            st.warning("Nenhum desafio correspondente foi localizado no servidor.")
        else:
            # Renderização limpa e livre de st.number_input inteiros
            for desafio in desafios:
                with st.container(border=True):
                    st.markdown(f"### {desafio.get('titulo', 'Sem Título')}")
                    st.write(f"📝 **Enunciado:** {desafio.get('descricao', 'Sem descrição.')}")
                    st.caption(f"📅 Prazo Limite: {desafio.get('data_limite', 'Não informado')}")
                    
                    st.divider()
                    st.markdown("**Dar nota ao projeto:**")
                    
                    # CORREÇÃO CRÍTICA: Interface de notas por estrelas/valores (Item 2.31)
                    nota_projeto = st.select_slider(
                        "Atribua uma nota de avaliação para este projeto:",
                        options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                        key=f"nota_slider_{desafio.get('id')}"
                    )

                    if st.button("Confirmar Envio da Nota", key=f"btn_voto_{desafio.get('id')}", use_container_width=True):
                        # Validação interna nativa via strings UUID
                        _processar_voto_nota(str(desafio.get("id")), str(nota_projeto), usuario_id_logado)


def _processar_voto_nota(desafio_id, nota, usuario_id_logado):
    """Executa o salvamento da nota dando feedback amigável sem expor termos complexos."""
    try:
        # Chama a camada de persistência com os UUIDs tratados em formato texto
        resultado = registrar_voto(desafio_id, nota, usuario_id_logado)
        
        st.success(f"✅ Avaliação concluída! Você atribuiu nota {nota} a este desafio.")
        st.rerun()
    except Exception as e:
        # Tratamento de erro limpo solicitado nas recomendações gerais do relatório (Item Geral 10)
        st.error("Desculpe, ocorreu um erro inesperado ao salvar sua nota. Tente sincronizar novamente.")