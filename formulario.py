import streamlit as st
import sqlite3
import re
import pandas as pd

# Carregar escolas
escolas_df = pd.read_excel("etcs.xlsx")

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

st.title("Cadastro de Coordenadores - Vestibulinho ETEC 2025.2")

# Botões de exportação e visualização
with st.expander("📄 Visualizar Cadastros e Exportar"):
    df = pd.read_sql_query("SELECT * FROM coordenadores", conn)
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar CSV", csv, "coordenadores.csv", "text/csv")

with st.form("form"):
    st.subheader("Informações da Unidade Escolar")
    regioes = sorted(escolas_df['Região Administrativa'].dropna().unique())
    regiao_default = regioes.index("Metropolitana de São Paulo") if "Metropolitana de São Paulo" in regioes else 0
    regiao_sel = st.selectbox("Região Administrativa", regioes, index=regiao_default)

    municipios_df = escolas_df[escolas_df['Região Administrativa'] == regiao_sel]
    municipios = sorted(municipios_df['Município'].dropna().unique())
    municipio_default = municipios.index("São Bernardo do Campo") if "São Bernardo do Campo" in municipios else 0
    municipio_sel = st.selectbox("Município", municipios, index=municipio_default)

    unidades_df = municipios_df[municipios_df['Município'] == municipio_sel][['Unidade', 'Endereço']]
    unidade_list = list(unidades_df['Unidade'])
    unidade_default = unidade_list.index("Etec Lauro Gomes") if "Etec Lauro Gomes" in unidade_list else 0
    unidade_sel = st.selectbox("Unidade (ETEC)", unidade_list, index=unidade_default)
    endereco = unidades_df.set_index('Unidade').loc[unidade_sel]['Endereço']
    st.text_input("Endereço completo da Unidade", value=endereco, disabled=True)

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
