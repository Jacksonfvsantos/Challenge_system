# 🎯 Sistema de Desafios

Bem-vindo ao repositório do **Sistema de Desafios**, uma plataforma interativa desenvolvida com [Streamlit](https://streamlit.io/) e [Supabase](https://supabase.com/). Este sistema foi desenhado para gerir desafios práticos, quizzes ao vivo, mini-provas e batalhas de equipes em um ambiente gamificado e educativo — desenvolvido para a AV3 de Laboratório e Desenvolvimento de Sistemas.

## 🔗 Links Úteis
* **Aplicação em Produção:** [Acessar o Sistema de Desafios](https://sistema-de-desafios.streamlit.app)

## ✨ Principais Funcionalidades
* **Autenticação de Usuários:** Registro e login com diferentes perfis (Aluno, Professor, Admin).
* **Central de Desafios:** Criação, submissão e gestão de desafios práticos operacionais.
* **Avaliações e Quizzes:** Mini-provas estruturadas e quizzes interativos em tempo real.
* **Batalha de Equipes:** Criação de equipes, gestão de capitães e competições síncronas/assíncronas.
* **Sistema de Votação:** Votação nos melhores projetos e submissões.
* **Painel de Administração:** Governança total da plataforma e gestão centralizada de acessos.

## 📂 Estrutura do Projeto

O projeto está organizado seguindo o padrão MVC adaptado para o ecossistema do Streamlit:

```text
sistema_de_desafios/
│
├── app.py                   # Ponto de entrada da aplicação (Main). O Streamlit executa a partir daqui.
├── requirements.txt         # Lista de dependências e bibliotecas do projeto.
│
├── .streamlit/
│   └── secrets.toml         # Variáveis de ambiente e chaves da API (informações sensíveis).
│
├── database/
│   └── conexao.py           # Configuração e conexão ao banco de dados (Supabase).
│
├── services/                # Camada de Regras de Negócio (Back-end)
│   ├── auth_service.py      # Lógica de autenticação e gestão de usuários.
│   ├── desafio_service.py   # Lógica de criação e validação de desafios.
│   ├── votacao_service.py   # Registro e contagem de votos.
│   ├── participacao_service.py # Gestão de submissões e entregas.
│   └── notificacao_service.py  # Sistema de alertas e logs de segurança.
│
├── telas/                   # Camada de Apresentação e Interface (Front-end / Telas)
│   ├── login.py, cadastro.py, home.py
│   ├── desafios.py, criar_desafios.py
│   ├── votacao.py, mini_provas.py, quiz_ao_vivo.py
│   ├── batalha_de_equipes.py
│   └── admin.py             # Painel exclusivo de governança do sistema.
│
├── utils/                   # Utilitários Globais
│   ├── session.py           # Controle da sessão ativa do usuário.
│   └── permissao.py         # Validação de acessos e permissões por perfil.
│
└── components/              # Componentes Visuais Reutilizáveis
    └── navbar.py            # Menu de navegação lateral (Sidebar) utilizado em todo o sistema.