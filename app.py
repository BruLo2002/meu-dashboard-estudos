import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Dashboard Concursos", layout="wide")

# --- BLOCO DE SEGURANÇA (O Porteiro) ---
def check_password():
    """Retorna True se o usuário digitar a senha correta."""
    # Se a senha ainda não foi verificada, marca como Falso
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    # Se já acertou antes, libera o acesso
    if st.session_state.password_correct:
        return True

    # Se não, mostra a caixa de senha
    st.markdown("### 🔒 Acesso Restrito")
    password = st.text_input("Digite a senha de acesso:", type="password")
    
    if password:
        # Verifica se a senha bate com a que está nos segredos (.streamlit/secrets.toml)
        if password == st.secrets["senha_acesso"]:
            st.session_state.password_correct = True
            st.rerun() # Recarrega a página para liberar o conteúdo
        else:
            st.error("Senha incorreta!")
    return False

# Chama a função. Se retornar False (senha errada), o app para de carregar aqui.
if not check_password():
    st.stop()

# Lista fixa de disciplinas
DISCIPLINAS = [
    "Português", "Matemática", "Raciocínio Lógico", 
    "Informática", "História", "Geografia", "Legislação", "Ética"
]

# --- CONEXÃO COM GOOGLE SHEETS ---
def conectar_gsheets():
    # O Streamlit Cloud vai ler as senhas dos "Segredos" (veremos na Missão 4)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Monta as credenciais usando os segredos do Streamlit
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    client = gspread.authorize(creds)
    # Abre a planilha pelo NOME (tem que ser exato)
    sheet = client.open("banco_de_questoes").sheet1 
    return sheet

# --- FUNÇÕES DE DADOS ---
def normalizar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    texto_sem_acento = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto_sem_acento.strip().title()

def carregar_dados():
    try:
        sheet = conectar_gsheets()
        data = sheet.get_all_records() # Baixa tudo da nuvem
        df = pd.DataFrame(data)
        
        # Se a planilha estiver vazia (só cabeçalho), retorna DF vazio estruturado
        if df.empty:
             return pd.DataFrame(columns=["Data", "Banca", "Disciplina", "Matéria", "Qtd_Questões", "Acertos", "Erros", "% Acerto"])

        # Tratamento de tipos
        cols_numericas = ["Qtd_Questões", "Acertos", "Erros", "% Acerto"]
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if "Matéria" in df.columns:
            df["Matéria"] = df["Matéria"].apply(normalizar_texto)
        
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no Google Sheets: {e}")
        return pd.DataFrame()

def salvar_na_nuvem(df):
    try:
        sheet = conectar_gsheets()
        sheet.clear() # Limpa a planilha antiga
        # Prepara os dados: inclui o cabeçalho e os valores
        dados_lista = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(dados_lista) # Escreve tudo de novo
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    div[data-baseweb="tab-list"] { gap: 10px; padding-top: 10px; }
    button[data-baseweb="tab"] { border-radius: 20px; border: 1px solid #4c4c4c; }
    button[data-baseweb="tab"][aria-selected="true"] { background-color: #FF4B4B; color: white; border-color: #FF4B4B; }
    </style>
""", unsafe_allow_html=True)

st.title("☁️ Dashboard de Performance (Online)")

# Carrega dados
df = carregar_dados()

# --- INTERFACE ---
tab1, tab2, tab3 = st.tabs(["📝 Registrar", "📊 Desempenho", "✏️ Editar"])

with tab1:
    st.header("Novo Registro")
    c1, c2 = st.columns(2)
    with c1:
        data_in = st.date_input("Data")
        banca = st.text_input("Banca").strip().upper()
        disciplina = st.selectbox("Disciplina", DISCIPLINAS)
    with c2:
        mat_raw = st.text_input("Matéria")
        materia = normalizar_texto(mat_raw) if mat_raw else ""
        qtd = st.number_input("Questões", min_value=1, step=1)
        acertos = st.number_input("Acertos", min_value=0, max_value=qtd, step=1)

    if st.button("Salvar na Nuvem"):
        erros = qtd - acertos
        pct = (acertos / qtd * 100)
        novo = {"Data": str(data_in), "Banca": banca, "Disciplina": disciplina, "Matéria": materia, 
                "Qtd_Questões": qtd, "Acertos": acertos, "Erros": erros, "% Acerto": round(pct, 2)}
        
        df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
        if salvar_na_nuvem(df):
            st.success("Salvo no Google Drive! 🚀")
            st.rerun()

with tab2:
    st.header("Visão Geral")
    if not df.empty:
        # Gráfico Geral
        df_disc = df.groupby("Disciplina")[["Qtd_Questões", "Acertos"]].sum().reset_index()
        df_disc["% Acerto"] = (df_disc["Acertos"]/df_disc["Qtd_Questões"]*100).fillna(0).round(2)
        fig = px.bar(df_disc, x="Disciplina", y="% Acerto", text="% Acerto", color="Disciplina", range_y=[0,120])
        fig.update_traces(textposition='outside', textfont=dict(size=14, weight='bold'))
        st.plotly_chart(fig, use_container_width=True)
        
        # Detalhes
        discs = sorted(df["Disciplina"].unique())
        if discs:
            abas = st.tabs(discs)
            for aba, d in zip(abas, discs):
                with aba:
                    dff = df[df["Disciplina"]==d]
                    df_ass = dff.groupby("Matéria")[["Qtd_Questões", "Acertos"]].sum().reset_index()
                    df_ass["% Acerto"] = (df_ass["Acertos"]/df_ass["Qtd_Questões"]*100).fillna(0).round(2)
                    fig2 = px.bar(df_ass, x="Matéria", y="% Acerto", text="% Acerto", color="% Acerto", color_continuous_scale="RdYlGn", range_y=[0,120])
                    fig2.update_traces(textposition='outside', textfont=dict(size=14, weight='bold'))
                    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.header("Editar Base")
    if not df.empty:
        df_edit = st.data_editor(df, num_rows="dynamic")
        if st.button("Salvar Edições na Nuvem"):
            # Recalcula
            df_edit["Qtd_Questões"] = pd.to_numeric(df_edit["Qtd_Questões"]).fillna(0)
            df_edit["Acertos"] = pd.to_numeric(df_edit["Acertos"]).fillna(0)
            df_edit["Matéria"] = df_edit["Matéria"].apply(normalizar_texto)
            df_edit["Erros"] = df_edit["Qtd_Questões"] - df_edit["Acertos"]
            df_edit["% Acerto"] = (df_edit["Acertos"]/df_edit["Qtd_Questões"]*100).fillna(0).round(2)
            
            if salvar_na_nuvem(df_edit):
                st.success("Base atualizada no Google!")
                st.rerun()