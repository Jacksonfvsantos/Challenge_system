import streamlit as st
<<<<<<< HEAD
from datetime import date, datetime
=======
from datetime import date
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
from services.batalha_de_equipes_service import (
    listar_batalhas, criar_batalha, finalizar_batalha
)
from utils.estilo import aplicar_estilo, cabecalho


<<<<<<< HEAD
def formatar_data_br(data_str):
    if not data_str: return "Sem prazo"
    try:
        data_limpa = str(data_str).split("T")[0]
        dt = datetime.strptime(data_limpa, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_str


def tela_batalha_gerenciar():
=======
def tela_batalha_gerenciar():

>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
    aplicar_estilo()

    usuario = st.session_state.usuario_logado
    tipo    = usuario.get("tipo_usuario", "aluno")
<<<<<<< HEAD
    user_id = str(usuario.get("id", "")).strip()

    if tipo not in ("professor", "admin"):
        st.error("Acesso restrito a professores corporativos.")
=======
    user_id = usuario.get("id")

    if tipo not in ("professor", "admin"):
        st.error("Acesso restrito a professores.")
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
        return

    cabecalho("Gerenciar Batalhas", "Crie e controle as batalhas de equipes")

<<<<<<< HEAD
    if st.button("⬅️ Voltar ao Módulo Principal"):
=======
    if st.button("Voltar"):
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
        st.session_state.pagina = "batalha_de_equipes"
        st.rerun()

    st.divider()
<<<<<<< HEAD
    st.markdown("### ⚔️ Nova Batalha")

    # Inicialização de estados para limpeza total automática pós-sucesso (Item 5.122)
    if "bat_titulo" not in st.session_state: st.session_state["bat_titulo"] = ""
    if "bat_desc" not in st.session_state: st.session_state["bat_desc"] = ""

    with st.container(border=True):
        titulo    = st.text_input("Título da batalha", value=st.session_state["bat_titulo"], placeholder="Ex: Batalha de Algoritmos")
        descricao = st.text_area("Descrição / Objetivo", value=st.session_state["bat_desc"], placeholder="Descreva o objetivo da batalha")

        col1, col2 = st.columns(2)
        with col1:
            quantidade_rodadas = st.number_input("Número de rodadas", min_value=1, step=1, value=3)
        with col2:
            tempo_por_rodada = st.number_input("Tempo por rodada (min)", min_value=1, step=1, value=30)

        prazo = st.date_input("Prazo Final de Execução", value=date.today(), min_value=date.today())

        regras = st.text_area("Regras de conduta", value="Siga as regras de Fair Play da instituição.")

        st.markdown("**Critérios de avaliação** (um por linha)")
        criterios_raw = st.text_area("Critérios", placeholder="Lógica\nOrganização\nCriatividade")
        criterios = [c.strip() for c in criterios_raw.splitlines() if c.strip()]

        with st.expander("🛡️ Configurações de Segurança Avançada", expanded=False):
            col3, col4, col5 = st.columns(3)
            with col3: bloquear_copia = st.checkbox("Bloquear cópia de código", value=True)
            with col4: verificar_plagio = st.checkbox("Mecanismo anti-plágio ativa", value=True)
            with col5: limitar_ip = st.checkbox("Limitar por endereço IP", value=False)
=======
    st.markdown("### Nova Batalha")

    with st.container(border=True):

        titulo    = st.text_input("Titulo da batalha", placeholder="Ex: Batalha de Algoritmos")
        descricao = st.text_area("Descricao / objetivo", placeholder="Descreva o objetivo da batalha")

        col1, col2 = st.columns(2)
        with col1:
            quantidade_rodadas = st.number_input("Numero de rodadas", min_value=1, step=1, value=3)
        with col2:
            tempo_por_rodada = st.number_input("Tempo por rodada (min)", min_value=1, step=1, value=30)

        prazo = st.date_input("Prazo", value=None, min_value=date.today())

        regras = st.text_area(
            "Regras de conduta",
            value="Siga as regras de Fair Play da instituicao."
        )

        st.markdown("**Criterios de avaliacao** (um por linha)")
        criterios_raw = st.text_area(
            "Criterios",
            placeholder="Logica\nOrganizacao\nCriatividade"
        )
        criterios = [c.strip() for c in criterios_raw.splitlines() if c.strip()]

        with st.expander("Configuracoes de seguranca", expanded=False):
            col3, col4, col5 = st.columns(3)
            with col3:
                bloquear_copia   = st.checkbox("Bloquear copia", value=True)
            with col4:
                verificar_plagio = st.checkbox("Verificar plagio", value=True)
            with col5:
                limitar_ip       = st.checkbox("Limitar IP", value=False)
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e

        seguranca = {
            "bloquear_copia":   bloquear_copia,
            "verificar_plagio": verificar_plagio,
            "limitar_IP":       limitar_ip
        }

<<<<<<< HEAD
        if st.button("Gravar e Lançar Batalha", use_container_width=True):
            if not titulo.strip():
                st.warning("O título é obrigatório.")
            else:
                batalhas_existentes = listar_batalhas()
                titulos_existentes  = [b.get("titulo", "").strip().lower() for b in batalhas_existentes if isinstance(b, dict)]
                
                if titulo.strip().lower() in titulos_existentes:
                    st.error(f"Já existe uma batalha registrada com o título '{titulo.strip()}'.")
                else:
                    prazo_iso = prazo.strftime("%Y-%m-%d")
                    if criar_batalha(titulo, descricao, user_id, quantidade_rodadas, tempo_por_rodada, criterios, regras, seguranca, prazo_iso):
                        st.success("✅ Batalha criada e disponibilizada com sucesso!") # Item 5.121
                        # Limpa completamente o formulário (Item 5.122)
                        st.session_state["bat_titulo"] = ""
                        st.session_state["bat_desc"] = ""
                        st.rerun()
                    else:
                        st.error("Erro operacional ao cadastrar batalha.")

    st.divider()
    st.markdown("### ⚔️ Batalhas Cadastradas")

    batalhas = listar_batalhas()
=======
        if st.button("Criar batalha", use_container_width=True):
            if not titulo.strip():
                st.warning("O titulo e obrigatorio.")
            else:
                batalhas_existentes = listar_batalhas()
                titulos_existentes  = [
                    b.get("titulo", "").strip().lower()
                    for b in batalhas_existentes
                    if isinstance(b, dict)
                ]
                if titulo.strip().lower() in titulos_existentes:
                    st.error(f"Ja existe uma batalha com o titulo '{titulo.strip()}'.")
                elif criar_batalha(
                    titulo, descricao, user_id,
                    quantidade_rodadas, tempo_por_rodada,
                    criterios, regras, seguranca, prazo
                ):
                    st.success("Batalha criada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao criar batalha.")

    st.divider()
    st.markdown("### Batalhas cadastradas")

    batalhas = listar_batalhas()

>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
    if not batalhas:
        st.info("Nenhuma batalha cadastrada ainda.")
        return

    for b in batalhas:
<<<<<<< HEAD
        bid = b.get("id")
        finalizada = b.get("finalizada", False)
        prazo_original = b.get('prazo')
        
        # CORREÇÃO CRÍTICA: Exibição em formato brasileiro solicitado (Item 5.118)
        prazo_br = formatar_data_br(prazo_original)

        # VALIDAÇÃO CRÍTICA: Verifica se o prazo já expirou hoje (Item 5.126 e 5.127)
        expirada = False
        if prazo_original:
            try:
                data_prazo = datetime.strptime(str(prazo_original).split("T")[0], "%Y-%m-%d").date()
                if data_prazo < date.today():
                    expirada = True
            except Exception:
                pass

        cor_status = "#ff4b4b" if expirada else "#90caf9" if finalizada else "#00b4d8"
        status_txt = "Prazo Expirado ⚠️" if expirada else "Finalizada 🛑" if finalizada else "Em Aberto 🟢"

        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <strong style="color:#0d1b2a; font-size:16px;">{b.get('titulo')}</strong>
                <span style="background:{cor_status}; color:#fff; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600;">{status_txt}</span>
            </div>
            <p style="color:#555; font-size:13px; margin:0;">
                Rodadas Previstas: {b.get('quantidade_rodadas','-')} &nbsp;|&nbsp;
                🗓️ Data Limite: <strong>{prazo_br}</strong>
            </p>
            """, unsafe_allow_html=True)

            if b.get("descricao"): st.caption(b["descricao"])

            # RESTRICAO SEVERA: Impede alteração se a batalha expirou (Item 5.126 e 5.127)
            if expirada:
                st.error("🔒 Edições bloqueadas: O prazo limite estabelecido para esta batalha já expirou.")
            elif not finalizada:
                if st.button("Finalizar Batalha Manualmente", key=f"fin_{bid}", use_container_width=True):
                    finalizar_batalha(bid)
                    st.success("Batalha encerrada com sucesso!")
                    st.rerun()
=======

        bid        = b.get("id")
        finalizada = b.get("finalizada", False)
        cor_status = "#00b4d8" if not finalizada else "#90caf9"
        status_txt = "Em aberto" if not finalizada else "Finalizada"

        with st.container(border=True):

            st.markdown(f"""
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:8px;
            ">
                <strong style="color:#0d1b2a; font-size:16px;">{b.get('titulo')}</strong>
                <span style="
                    background:{cor_status};
                    color:#fff;
                    padding:3px 10px;
                    border-radius:20px;
                    font-size:12px;
                    font-weight:600;
                ">{status_txt}</span>
            </div>
            <p style="color:#555; font-size:13px; margin:0;">
                Rodadas: {b.get('quantidade_rodadas','-')} &nbsp;|&nbsp;
                Prazo: {b.get('prazo') or 'sem prazo'}
            </p>
            """, unsafe_allow_html=True)

            if b.get("descricao"):
                st.caption(b["descricao"])

            criterios_lista = b.get("criterios_avaliacao") or []
            if criterios_lista:
                with st.expander("Criterios"):
                    for c in criterios_lista:
                        st.markdown(f"- {c}")

            if b.get("regras_conduta"):
                with st.expander("Regras"):
                    st.write(b["regras_conduta"])

            if not finalizada:
                if st.button("Finalizar batalha", key=f"fin_{bid}", use_container_width=True):
                    finalizar_batalha(bid)
                    st.success("Batalha finalizada.")
                    st.rerun()
>>>>>>> 55ea97eb78baf814069a38414777bcba0ff8e98e
