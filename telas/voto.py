import streamlit as st
import pandas as pd
from services.votacao_service import (
    buscar_voto_usuario,
    registrar_voto,
    atualizar_voto,
    deletar_voto,
    listar_votos_desafio,
    analisar_fair_play_ia
)
from utils.estilo import aplicar_estilo, cabecalho

def tela_voto():
    aplicar_estilo()
    
    if "desafio_voto" not in st.session_state or not st.session_state.desafio_voto:
        st.warning("Nenhum desafio selecionado.")
        if st.button("Voltar"):
            st.session_state.pagina = "votacao"
            st.rerun()
        return

    desafio = st.session_state.desafio_voto
    usuario = st.session_state.usuario_logado
    cabecalho(desafio["titulo"], f"Prazo: {desafio.get('data_limite', '-')}")

    if st.button("Voltar para votação"):
        st.session_state.pagina = "votacao"
        st.rerun()

    st.divider()
    
    st.markdown("### Avaliar Projeto")
    opcoes = ["Bom", "Regular", "Ruim"]
    voto = st.radio("Escolha seu voto:", opcoes, key="radio_voto")
    
    comentario = st.text_area("Justifique sua nota (obrigatório para análise de Fair Play):", 
                             placeholder="Descreva tecnicamente o que observou no projeto...")
    
    if st.button("Confirmar Envio do Voto", type="primary", use_container_width=True):
        if not comentario or len(comentario) < 15:
            st.warning("⚠️ Por favor, escreva uma justificativa técnica com pelo menos 15 caracteres para validar seu voto.")
        else:
            with st.spinner("Analisando integridade do voto com IA..."):
                api_key = st.secrets.get("GEMINI_API_KEY")
                score_ia = analisar_fair_play_ia(comentario, api_key)
                
                registrar_voto(
                    usuario["email"], 
                    desafio["titulo"], 
                    voto, 
                    comentario, 
                    score_ia
                )
                st.success(f"✅ Voto registrado! (Score de Auditoria: {score_ia}/100)")
                st.rerun()

    st.divider()
    
    if st.button("Mostrar / Ocultar resultados"):
        st.session_state.mostrar_resultado = not st.session_state.get("mostrar_resultado", False)
        st.rerun()

    if st.session_state.get("mostrar_resultado"):
        votos = listar_votos_desafio(desafio["titulo"])
        if not votos:
            st.info("Nenhum voto registrado.")
        else:
            df = pd.DataFrame(votos)
            st.markdown("### Resultados e Auditoria")
            st.bar_chart(df["voto"].value_counts())
            
            if usuario.get("tipo_usuario") in ("professor", "admin"):
                st.markdown("#### Auditoria de Fair Play (IA)")
                st.dataframe(df[["usuario", "voto", "comentario", "analise_ia_score"]])