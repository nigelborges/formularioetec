import streamlit as st
import pandas as pd

# Carrega e limpa o arquivo
df = pd.read_excel("etcs.xlsx")
df = df.astype(str).apply(lambda x: x.str.strip())

st.title("Teste de Filtro de ETECs")

# REGIÃO
regioes = sorted(df['Região Administrativa'].unique())
regiao_sel = st.selectbox("Região Administrativa", regioes)

# MUNICÍPIO
df_municipios = df[df['Região Administrativa'] == regiao_sel]
municipios = sorted(df_municipios['Município'].unique())
municipio_sel = st.selectbox("Município", municipios)

# UNIDADE
df_unidades = df_municipios[df_municipios['Município'] == municipio_sel]
unidades = sorted(df_unidades['Unidade'].unique())
unidade_sel = st.selectbox("Unidade (ETEC)", unidades)

# ENDEREÇO
endereco = df_unidades[df_unidades['Unidade'] == unidade_sel]['Endereço'].values[0]
st.text_input("Endereço", value=endereco, disabled=True)
