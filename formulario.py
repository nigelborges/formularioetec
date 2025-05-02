import streamlit as st
import sqlite3
import re
import pandas as pd
from PIL import Image

# Carregar escolas com limpeza de espaços
try:
    escolas_df = pd.read_excel("etcs.xlsx")
    escolas_df = escolas_df.astype(str).apply(lambda x: x.str.strip())
except Exception as e:
    st.error(f"Erro ao carregar etcs.xlsx: {e}")
    st.stop()

# Banco de dados
conn = sqlite3.connect("etec.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS coordenadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    telefone TEXT,
    cpf TEXT,
    banco TEXT,
    agencia TEXT,
    conta TEXT,
    tipo_chave TEXT,
    chave_pix TEXT,
    unidade TEXT,
    endereco TEXT,
    centro_distribuicao TEXT,
    coordenador_prova TEXT,
    divulgacao TEXT,
    outros_meios TEXT,
    observacoes TEXT
)
''')
conn.commit()

# Logo acima do título
logo = Image.open("idecan.png")
st.image(logo, width=350)
st.title("Cadastro de Coordenadores - Vestibulinho ETEC 2025.2")

# Filtros dinâmicos fora do form
st.subheader("Informações da Unidade Escolar")
regioes = sorted(escolas_df['Região Administrativa'].unique())
regiao_sel = st.selectbox("Região Administrativa", regioes)

df_municipios = escolas_df[escolas_df['Região Administrativa'] == regiao_sel]
municipios = sorted(df_municipios['Município'].unique())
municipio_sel = st.selectbox("Município", municipios)

df_unidades = df_municipios[df_municipios['Município'] == municipio_sel]
unidades = sorted(df_unidades['Unidade'].unique())
unidade_sel = st.selectbox("Unidade (ETEC)", unidades)

endereco = df_unidades[df_unidades['Unidade'] == unidade_sel]['Endereço'].values[0]
st.text_input("Endereço completo da Unidade", value=endereco, disabled=True)

# Formulário principal
with st.form("form"):
    st.subheader("Dados Pessoais")
    nome = st.text_input("Nome completo")
    telefone = st.text_input("Telefone de contato (apenas números)")
    cpf = st.text_input("CPF (somente números)")

    st.subheader("Dados Bancários")
    banco = st.text_input("Banco")
    agencia = st.text_input("Agência")
    conta = st.text_input("Conta (com dígito)")
    tipo_chave = st.selectbox("Tipo de chave Pix", ["CPF", "Telefone", "E-mail", "Aleatória"])
    chave_pix = st.text_input("Chave Pix")

    st.subheader("Funções no Processo Seletivo")
    centro_distribuicao = st.radio("Sua unidade gostaria de ser Centro de Distribuição?", ["Sim", "Não"])
    coordenador_prova = st.radio("Você será Coordenador de Local de Prova?", ["Sim", "Não"])

    divulgacao = st.multiselect("Meio(s) de Divulgação mais efetivo(s) para o Vestibulinho", [
        "Tráfego Pago", "Propaganda em TV", "Distribuição Física de Panfletos e Flyers",
        "Cartazes/Banners em Locais de Grande Circulação", "Busdoor/Outdoor", "Outros"])

    outros_meios = ""
    if "Outros" in divulgacao:
        outros_meios = st.text_input("Quais?")

    observacoes = st.text_area("Observações e Sugestões")

    submitted = st.form_submit_button("Enviar")

    if submitted:
        if not (re.fullmatch(r'\d{11}', cpf) and re.fullmatch(r'\d{10,11}', telefone)):
            st.error("CPF ou telefone inválido. Verifique e tente novamente.")
        else:
            cursor.execute('''
                INSERT INTO coordenadores (
                    nome, telefone, cpf, banco, agencia, conta,
                    tipo_chave, chave_pix, unidade, endereco,
                    centro_distribuicao, coordenador_prova, divulgacao,
                    outros_meios, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nome, telefone, cpf, banco, agencia, conta, tipo_chave, chave_pix,
                unidade_sel, endereco, centro_distribuicao, coordenador_prova,
                ", ".join(divulgacao), outros_meios, observacoes
            ))
            conn.commit()
            st.success("Cadastro realizado com sucesso!")
