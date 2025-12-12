import streamlit as st
import pandas as pd
import plotly.express as px
import os
import unicodedata

# Nome do arquivo onde os dados serão salvos
ARQUIVO_DADOS = 'banco_de_questoes.csv'

# Lista fixa de disciplinas
DISCIPLINAS = [
    "Português",
    "Matemática",
    "Raciocínio Lógico",
    "Informática",
    "História",
    "Geografia",
    "Legislação",
    "Ética"
]

# --- FUNÇÃO DE FAXINA (Corrige acentos e textos estranhos) ---
def normalizar_texto(texto):
    if not isinstance(texto, str):
        return str(texto)
    # Remove acentos (ex: "Divisão" vira "Divisao")
    texto_sem_acento = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto_sem_acento.strip().title()

# --- CARREGAR DADOS COM SEGURANÇA ---
def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return pd.DataFrame(columns=["Data", "Banca", "Disciplina", "Matéria", "Qtd_Questões", "Acertos", "Erros", "% Acerto"])
    
    df = pd.read_csv(ARQUIVO_DADOS)
    
    # FORÇA TUDO QUE É NÚMERO A SER NÚMERO
    cols_numericas = ["Qtd_Questões", "Acertos", "Erros", "% Acerto"]
    for col in cols_numericas:
        if col in df.columns:
            # 'coerce' transforma texto ruim em NaN, e fillna(0) transforma NaN em 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # APLICA A FAXINA NOS TEXTOS
    if "Matéria" in df.columns:
        df["Matéria"] = df["Matéria"].apply(normalizar_texto)
    if "Banca" in df.columns:
        df["Banca"] = df["Banca"].astype(str).str.strip().str.upper()
            
    return df

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

# --- ESTILIZAÇÃO CSS (BOTOES BONITOS) ---
def aplicar_estilo_visual():
    st.markdown("""
        <style>
        div[data-baseweb="tab-list"] { gap: 10px; padding-top: 10px; padding-bottom: 10px; }
        button[data-baseweb="tab"] {
            background-color: transparent; border: 1px solid #4c4c4c; border-radius: 20px;
            padding: 8px 20px; font-size: 14px; transition: all 0.3s ease; margin-top: 0px;
        }
        button[data-baseweb="tab"]:hover {
            background-color: #2b2b2b; border-color: #FF4B4B; transform: translateY(-3px); color: #FF4B4B;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: #FF4B4B; color: white; border-color: #FF4B4B;
            font-weight: bold; box-shadow: 0px 4px 10px rgba(255, 75, 75, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

# --- INÍCIO DO APP ---
st.set_page_config(page_title="Dashboard Concursos", layout="wide")
aplicar_estilo_visual()
st.title("📚 Dashboard de Performance")

df = carregar_dados()

# --- ABAS PRINCIPAIS ---
tab1, tab2, tab3 = st.tabs(["📝 Registrar Estudo", "📊 Análise de Desempenho", "✏️ Editar/Excluir"])

# 1. ABA REGISTRAR
with tab1:
    st.header("Novo Registro")
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data do Estudo")
        banca = st.text_input("Banca (ex: Cebraspe)").strip().upper()
        disciplina = st.selectbox("Disciplina", DISCIPLINAS)
    with col2:
        entrada_materia_raw = st.text_input("Matéria/Assunto (ex: Crase)")
        # Normaliza imediatamente ao digitar
        entrada_materia = normalizar_texto(entrada_materia_raw) if entrada_materia_raw else ""
        
        qtd_questoes = st.number_input("Total de Questões", min_value=1, step=1)
        acertos = st.number_input("Total de Acertos", min_value=0, max_value=qtd_questoes, step=1)

    if st.button("Salvar Registro"):
        erros = qtd_questoes - acertos
        porcentagem = (acertos / qtd_questoes) * 100 if qtd_questoes > 0 else 0

        novo_registro = {
            "Data": str(data),
            "Banca": banca,
            "Disciplina": disciplina,
            "Matéria": entrada_materia,
            "Qtd_Questões": qtd_questoes,
            "Acertos": acertos,
            "Erros": erros,
            "% Acerto": round(porcentagem, 2)
        }
        
        # Salva direto
        df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
        salvar_dados(df)
        st.success(f"✅ Registrado: {disciplina} - {entrada_materia}")

# 2. ABA DESEMPENHO
with tab2:
    st.header("📊 Visão Geral")
    if df.empty:
        st.info("Nenhum dado registrado ainda.")
    else:
        # Gráfico Geral
        st.subheader("1. Desempenho Geral")
        df_disc = df.groupby("Disciplina")[["Qtd_Questões", "Acertos"]].sum().reset_index()
        df_disc["% Acerto"] = (df_disc["Acertos"] / df_disc["Qtd_Questões"] * 100).fillna(0).round(2)
        
        fig_geral = px.bar(df_disc, x="Disciplina", y="% Acerto", color="Disciplina", text="% Acerto", range_y=[0, 120])
        fig_geral.update_traces(texttemplate='%{y:.1f}%', textposition='outside', textfont=dict(size=16, weight='bold'))
        fig_geral.update_layout(font=dict(size=14), xaxis_title_font=dict(size=20, weight='bold'), yaxis_title_font=dict(size=18, weight='bold'))
        st.plotly_chart(fig_geral, use_container_width=True)
        
        st.divider()
        
        # Gráfico Detalhado
        st.subheader("2. Raio-X da Matéria (Selecione abaixo)")
        disciplinas_ativas = sorted(list(df["Disciplina"].unique()))
        
        if not disciplinas_ativas:
            st.write("Sem dados.")
        else:
            abas_materias = st.tabs(disciplinas_ativas)
            for aba, disc_atual in zip(abas_materias, disciplinas_ativas):
                with aba:
                    df_filtrado = df[df["Disciplina"] == disc_atual]
                    df_assuntos = df_filtrado.groupby("Matéria")[["Qtd_Questões", "Acertos"]].sum().reset_index()
                    df_assuntos["% Acerto"] = (df_assuntos["Acertos"] / df_assuntos["Qtd_Questões"] * 100).fillna(0).round(2)
                    
                    c1, c2, c3 = st.columns(3)
                    qtd = int(df_filtrado["Qtd_Questões"].sum())
                    med = (df_filtrado["Acertos"].sum() / qtd * 100) if qtd > 0 else 0
                    c1.metric("Questões Totais", qtd)
                    c2.metric("Média da Disciplina", f"{med:.1f}%")
                    c3.metric("Tópicos Estudados", len(df_assuntos))

                    fig_detalhe = px.bar(df_assuntos, x="Matéria", y="% Acerto", text="% Acerto", color="% Acerto", color_continuous_scale="RdYlGn", range_y=[0, 120])
                    fig_detalhe.update_traces(texttemplate='%{y:.1f}%', textposition='outside', textfont=dict(size=16, weight='bold'))
                    fig_detalhe.update_layout(font=dict(size=14), xaxis_title_font=dict(size=20, weight='bold'), yaxis_title_font=dict(size=18, weight='bold'))
                    st.plotly_chart(fig_detalhe, use_container_width=True)

# 3. ABA EDITAR
with tab3:
    st.header("Gerenciar Registros")
    if not df.empty:
        st.info("Obs: Seus textos foram padronizados (sem acentos) para evitar duplicações.")
        df_editado = st.data_editor(df, num_rows="dynamic", column_config={"% Acerto": st.column_config.NumberColumn(disabled=True)})
        if st.button("Salvar Alterações"):
            # Recalcula tudo com segurança
            df_editado["Qtd_Questões"] = pd.to_numeric(df_editado["Qtd_Questões"], errors='coerce').fillna(0)
            df_editado["Acertos"] = pd.to_numeric(df_editado["Acertos"], errors='coerce').fillna(0)
            df_editado["Matéria"] = df_editado["Matéria"].apply(normalizar_texto)
            df_editado["Erros"] = df_editado["Qtd_Questões"] - df_editado["Acertos"]
            
            # Evita divisão por zero
            df_editado["% Acerto"] = df_editado.apply(lambda x: (x["Acertos"] / x["Qtd_Questões"] * 100) if x["Qtd_Questões"] > 0 else 0, axis=1).round(2)
            
            salvar_dados(df_editado)
            st.success("Salvo com sucesso!")
            st.rerun()