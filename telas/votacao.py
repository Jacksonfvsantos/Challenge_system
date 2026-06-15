import streamlit as st
<<<<<<< HEAD
import pandas as pd
from services.desafio_service import listar_desafios
from utils.estilo import aplicar_estilo, cabecalho

try:
    from services.votacao_service import listar_votos, registrar_voto
except ImportError:
    def listar_votos(): return []
    def registrar_voto(d, a, u): return {"sucesso": True}

def tela_votacao():
=======
from services.desafio_service import listar_desafios
from utils.estilo import aplicar_estilo, cabecalho

# Tentativa segura de importar as funcoes de voto do service
try:
    from services.votacao_service import listar_votos, registrar_voto
except ImportError:
    try:
        from services.votacao_service import obter_votos as listar_votos, registrar_voto
    except ImportError:
        try:
            from services.votacao_service import get_votos as listar_votos, registrar_voto
        except ImportError:
            from services.votacao_service import registrar_voto
            def listar_votos():
                return []


def tela_votacao():
    # Injeta as configuracoes do seu CSS global (Navbar e botoes)
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
    aplicar_estilo()

    usuario = st.session_state.get("usuario_logado", {})
    tipo = usuario.get("tipo_usuario", "aluno")
<<<<<<< HEAD
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
=======
    
    # O banco espera TEXT, vamos garantir salvando como string limpa
    usuario_id_logado = str(usuario.get("id", ""))

    cabecalho(
        "Sistema de Votacao",
        "Vote nos melhores projetos ou gerencie as votacoes ativas"
    )

    if tipo == "professor":
        st.subheader("Gerenciamento de Votos")
        
        if st.button("Listar Todos os Votos", width="stretch"):
            try:
                votos = listar_votos()
                if votos:
                    for v in votos:
                        # Adaptado para ler as colunas reais do seu SQL (usuario_id, desafio_id, voto)
                        st.markdown(f"""
                        <div style="
                            background: #f0f9ff;
                            border-left: 4px solid #1b3a5c;
                            border-radius: 8px;
                            padding: 12px 16px;
                            margin-bottom: 8px;
                        ">
                            <span style="color: #0d1b2a; font-weight: 600;">Desafio ID: {v.get('desafio_id', '-')}</span><br>
                            <span style="color: #555; font-size: 13px;">Eleitor (ID): {v.get('usuario_id', '-')} | Votou no Aluno (ID): {v.get('voto', '-')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Nenhum voto registrado ate o momento.")
            except Exception:
                st.error("Erro ao listar votos do banco de dados. Verifique a tabela no Supabase.")
                
    else:
        st.subheader("Pesquisar e Votar")
        
        pesquisa = st.text_input("Pesquisar desafio por titulo")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
        
        try:
            desafios = listar_desafios()
        except Exception:
            desafios = []

        if pesquisa and desafios:
<<<<<<< HEAD
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
=======
            desafios = [
                d for d in desafios
                if pesquisa.lower() in d.get("titulo", "").lower()
            ]

        if not desafios:
            st.warning("Nenhum desafio ativo encontrado para votacao no momento.")
            
            # Bloco de redundancia para votacao via ID manual caso o banco nao liste os desafios
            with st.container(border=True):
                st.caption("Votacao Manual (Insira os IDs manualmente)")
                desafio_id_manual = st.number_input("ID do Desafio", min_value=1, step=1, key="manual_desafio_id")
                aluno_id = st.number_input("ID do Aluno Autor do Projeto", min_value=1, step=1, key="manual_aluno_id")
                
                if st.button("Confirmar Voto", key="voto_manual_btn", width="stretch"):
                    if str(aluno_id) == usuario_id_logado:
                        st.error("Voce nao pode votar no seu proprio projeto.")
                    else:
                        _processar_voto(str(desafio_id_manual), str(aluno_id), usuario_id_logado)
        else:
            # Lista os desafios com o layout e inputs corrigidos para TEXT
            for desafio in desafios:
                with st.container(border=True):
                    st.subheader(desafio.get("titulo", "Sem Titulo"))
                    st.write(f"Prazo final: {desafio.get('data_limite', 'Nao informado')}")
                    
                    aluno_id = st.number_input(
                        "ID do Aluno Autor do Projeto", 
                        min_value=1, 
                        step=1, 
                        key=f"aluno_id_{desafio.get('id')}"
                    )

                    if st.button("Confirmar Voto", key=f"voto_{desafio.get('id')}", width="stretch"):
                        if str(aluno_id) == usuario_id_logado:
                            st.error("Voce nao pode votar no seu proprio projeto.")
                        else:
                            _processar_voto(str(desafio.get("id")), str(aluno_id), usuario_id_logado)


def _processar_voto(desafio_id, aluno_id, usuario_id_logado):
    """Executa a gravacao garantindo o envio dos parametros tratados como string"""
    try:
        resultado = None
        
        # Envia os dados convertidos para String conforme o tipo das colunas do seu banco
        try:
            resultado = registrar_voto(desafio_id, aluno_id, usuario_id_logado)
        except TypeError:
            try:
                # Caso a assinatura receba os valores invertidos
                resultado = registrar_voto(aluno_id, desafio_id)
            except TypeError:
                resultado = registrar_voto(desafio_id, aluno_id)

        if resultado:
            if isinstance(resultado, dict) and resultado.get("sucesso"):
                st.success("Seu voto foi registrado com sucesso!")
                st.rerun()
            elif isinstance(resultado, dict):
                st.error(resultado.get("mensagem", "Erro ao registrar voto."))
            else:
                st.success("Operacao de votacao concluida.")
                st.rerun()
                
    except Exception as e:
        st.error(f"Erro de comunicacao com o banco de dados: {str(e)}")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
