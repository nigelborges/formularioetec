import streamlit as st
import sqlite3
import re

db = sqlite3.connect("etec.db", check_same_thread=False)
cursor = db.cursor()

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
db.commit()

st.title("Cadastro de Coordenadores - Vestibulinho ETEC 2025.2")

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

    st.subheader("Informações da Unidade Escolar")
    unidade = st.text_input("Nome da Unidade (ETEC)")
    endereco = st.text_input("Endereço completo da Unidade")

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
                unidade, endereco, centro_distribuicao, coordenador_prova,
                ", ".join(divulgacao), outros_meios, observacoes
            ))
            db.commit()
            st.success("Cadastro realizado com sucesso!")
