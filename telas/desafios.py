import streamlit as st
from datetime import datetime
from utils.estilo import aplicar_estilo, cabecalho, renderizar_card
from services.desafio_service import listar_desafios

def tela_desafios():
    aplicar_estilo()
    cabecalho("Central de Desafios", "Explore os desafios disponíveis ou crie novos.")

    desafios = listar_desafios() or []
    for desafio in desafios:
        footer = f"Nível: {desafio.get('nivel_dificuldade', 'N/A')} | 📅 Prazo: {desafio.get('data_limite', 'Sem prazo')}"
        renderizar_card(
            titulo=desafio.get('titulo', 'Sem Título'),
            descricao=desafio.get('descricao', 'Sem descrição.'),
            cor_borda="#1b3a5c",
            footer=footer
        )