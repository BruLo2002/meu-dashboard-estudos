import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Dashboard Concursos", layout="wide")

# --- FUNÇÃO DE AUTENTICAÇÃO (Barra Lateral) ---
def verificar_permissao():
    """Verifica a senha na sidebar para liberar funções de Admin"""
    with st.sidebar:
        st.header("🔐 Acesso Administrativo")
        senha_digitada = st.text_input("Senha de Admin:", type="password")
        
        # Verifica se a senha bate com o segredo configurado no Streamlit Cloud
        if senha_digitada == st.secrets["senha_acesso"]:
            st.success("Logado como Admin ✅")
            return True
        elif senha_digitada:
            st.error("Senha incorreta ❌")
        else:
            st.info("👀 Modo Visitante Ativo")
        return False

# Executa a verificação
is_admin = verificar_permissao()

# Lista fixa de disciplinas
DISCIPLINAS = [
    "Português", "Matemática", "Raciocínio Lógico", 
    "Informática", "História", "Geografia", "Legislação", "Ética"
]

# --- CONEXÃO COM GOOGLE SHEETS ---
def conectar_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
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
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
             return pd.DataFrame(columns=["Data", "Banca", "Disciplina", "Matéria", "Qtd_Questões", "Acertos", "Erros", "% Acerto"])

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
        sheet.clear()
        dados_lista = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(dados_lista)
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

# --- INÍCIO DO APP ---
st.title("☁️ Dashboard de Performance (Online)")

# Carrega dados (Visível para todos)
df = carregar_dados()

# --- DEFINIÇÃO DINÂMICA DAS ABAS ---
if is_admin:
    # Se for admin, vê todas as opções
    tab_dash, tab_reg, tab_edit = st.tabs(["📊 Desempenho (Público)", "📝 Registrar (Admin)", "✏️ Editar (Admin)"])
else:
    # Se for visitante, vê apenas o gráfico
    tab_dash, = st.tabs(["📊 Desempenho (Público)"])
    tab_reg = None
    tab_edit = None

# --- ABA 1: DESEMPENHO (PÚBLICA) ---
with tab_dash:
    st.header("Visão Geral")
    if not df.empty:
        # Gráfico Geral
        df_disc = df.groupby("Disciplina")[["Qtd_Questões", "Acertos"]].sum().reset_index()
        # Tratamento para evitar divisão por zero
        df_disc["% Acerto"] = df_disc.apply(lambda x: (x["Acertos"]/x["Qtd_Questões"]*100) if x["Qtd_Questões"] > 0 else 0, axis=1).round(2)
        
        fig = px.bar(df_disc, x="Disciplina", y="% Acerto", text="% Acerto", color="Disciplina", range_y=[0,120])
        fig.update_traces(textposition='outside', textfont=dict(size=14, weight='bold'))
        st.plotly_chart(fig, use_container_width=True)
        
        # Detalhes
        discs = sorted(df["Disciplina"].unique())
        if discs:
            st.subheader("Raio-X por Matéria")
            abas_materias = st.tabs(discs)
            for aba, d in zip(abas_materias, discs):
                with aba:
                    dff = df[df["Disciplina"]==d]
                    df_ass = dff.groupby("Matéria")[["Qtd_Questões", "Acertos"]].sum().reset_index()
                    df_ass["% Acerto"] = df_ass.apply(lambda x: (x["Acertos"]/x["Qtd_Questões"]*100) if x["Qtd_Questões"] > 0 else 0, axis=1).round(2)
                    
                    fig2 = px.bar(df_ass, x="Matéria", y="% Acerto", text="% Acerto", color="% Acerto", color_continuous_scale="RdYlGn", range_y=[0,120])
                    fig2.update_traces(textposition='outside', textfont=dict(size=14, weight='bold'))
                    st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Nenhum dado registrado ainda.")

# --- ABA 2: REGISTRAR (SÓ ADMIN) ---
if is_admin and tab_reg:
    with tab_reg:
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
            pct = (acertos / qtd * 100) if qtd > 0 else 0
            novo = {"Data": str(data_in), "Banca": banca, "Disciplina": disciplina, "Matéria": materia, 
                    "Qtd_Questões": qtd, "Acertos": acertos, "Erros": erros, "% Acerto": round(pct, 2)}
            
            df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
            if salvar_na_nuvem(df):
                st.success("Salvo no Google Drive! 🚀")
                st.rerun()

# --- ABA 3: EDITAR (SÓ ADMIN) ---
if is_admin and tab_edit:
    with tab_edit:
        st.header("Editar Banco")
        if not df.empty:
            df_edit = st.data_editor(df, num_rows="dynamic")
            if st.button("Salvar Edições na Nuvem"):
                # Recalcula
                df_edit["Qtd_Questões"] = pd.to_numeric(df_edit["Qtd_Questões"]).fillna(0)
                df_edit["Acertos"] = pd.to_numeric(df_edit["Acertos"]).fillna(0)
                df_edit["Matéria"] = df_edit["Matéria"].apply(normalizar_texto)
                df_edit["Erros"] = df_edit["Qtd_Questões"] - df_edit["Acertos"]
                
                # Cálculo seguro de %
                df_edit["% Acerto"] = df_edit.apply(lambda x: (x["Acertos"]/x["Qtd_Questões"]*100) if x["Qtd_Questões"] > 0 else 0, axis=1).round(2)
                
                if salvar_na_nuvem(df_edit):
                    st.success("Base atualizada no Google!")
                    st.rerun()