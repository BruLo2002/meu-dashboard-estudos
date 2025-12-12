# 📊 Dashboard de Performance em Concursos

> Um Web App Full Stack para registrar sessões de estudo e analisar desempenho por disciplina e matéria através de dados e gráficos interativos.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://meu-dashboard-estudos-srccpftx3altxrqmx224b3.streamlit.app/)

## 🖼️ Visão Geral

Este projeto foi desenvolvido com o objetivo de aplicar conceitos de Ciência de Dados para resolver um problema real: o gerenciamento de estudos para concursos públicos.

Diferente de planilhas estáticas, este dashboard oferece uma interface dinâmica conectada à nuvem, permitindo o registro de questões e a análise de métricas de acertos em tempo real, acessível via desktop ou mobile.

### 📸 Screenshots

![Tela Principal](https://github.com/user-attachments/assets/e4d12272-2b5a-4bf8-845a-6cc205e67699)

![Desempenho](https://github.com/user-attachments/assets/e647b483-5f1c-4e8c-8fa3-66c36c767b55)
*Visão geral do desempenho por disciplina.*

## 🎯 Funcionalidades Principais

- **Registro de Estudos (CRUD):** Formulário para input de Data, Banca, Disciplina, Matéria e Quantidade de Acertos/Erros.
- **Integração Cloud (Backend):** Conexão via API com o **Google Sheets**, funcionando como banco de dados persistente.
- **Análise Exploratória:**
    - Gráficos de barras gerais por disciplina.
    - **Raio-X Detalhado:** Drill-down para visualizar o desempenho por tópico específico dentro de cada matéria.
    - Indicadores visuais de performance (gradiente de cores).
- **Tratamento de Dados:** Normalização automática de texto (remoção de acentos e padronização) para evitar duplicidade de registros.
- **Sistema de Edição:** Interface tabular para correção de registros lançados erroneamente.
- **Controle de Acesso (RBAC):** Sistema de segurança com níveis de permissão.
    - **Modo Visitante:** Acesso público apenas para visualização dos dashboards (Leitura).
    - **Modo Admin:** Acesso protegido por senha para inserção e edição de dados (Escrita).

## 🛠️ Tecnologias Utilizadas

O projeto foi construído 100% em Python, utilizando as seguintes bibliotecas e ferramentas:

* **[Streamlit](https://streamlit.io/):** Framework para construção da interface web (Front-end).
* **[Pandas](https://pandas.pydata.org/):** Manipulação, limpeza e agregação dos dados (ETL).
* **[Plotly Express](https://plotly.com/python/plotly-express/):** Visualização de dados interativa.
* **[Google Sheets API (gspread)](https://docs.gspread.org/):** Conexão e autenticação com o Google Cloud Platform.
* **[Streamlit Cloud](https://share.streamlit.io/):** Deploy e hospedagem da aplicação.

## 🚀 Como rodar o projeto localmente

Para executar este projeto na sua máquina, você precisará das credenciais de uma conta de serviço do Google (GCP).

### Pré-requisitos
* Python 3.8+
* Conta no Google Cloud Platform com APIs "Sheets" e "Drive" ativadas.

### Passo a Passo

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/BruLo2002/meu-dashboard-estudos.git
    cd meu-dashboard-estudos
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure as Credenciais:**
    * Crie uma pasta chamada `.streamlit` na raiz do projeto.
    * Crie um arquivo `secrets.toml` dentro dela seguindo o modelo abaixo, preenchendo com os dados do seu arquivo JSON do Google:

    ```toml
    [gcp_service_account]
    type = "service_account"
    project_id = "seu-project-id"
    private_key = "-----BEGIN PRIVATE KEY-----..."
    client_email = "seu-email-bot@..."
    # ... adicione os outros campos do seu JSON
    ```

4.  **Execute a aplicação:**
    ```bash
    streamlit run app.py
    ```

---

## 👨‍💻 Autor

Desenvolvido por **Bruno Lopes Paulino**.

Estudante de Ciência e Tecnologia - UFABC.
