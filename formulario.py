import streamlit as st
import sqlite3
import re
import pandas as pd
from PIL import Image
import base64
from io import BytesIO

# ==== LOGO BASE64 PRE-CARREGADA ====
def get_image_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode()

logo = Image.open("idecan.png")
logo_base64 = get_image_base64(logo)

# ==== USUÁRIOS E SENHAS ====
usuarios = {
    "admin": {"senha": "IDECAN2025", "tipo": "admin"},
    "cadastro": {"senha": "idecan123", "tipo": "comum"},
    "usuario1": {"senha": "123", "tipo": "comum"},
}

# LOGIN CENTRALIZADO
if "usuario" not in st.session_state:
    st.markdown(f"""
        <div style='text-align: center;'>
            <img src='data:image/png;base64,{logo_base64}' width='250'>
            <h2>🔐 Acesso ao Sistema</h2>
        </div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")
        login_submit = st.form_submit_button("Entrar")

    if login_submit:
        usuario_logado = usuarios.get(usuario_input)
        if usuario_logado and senha_input == usuario_logado["senha"]:
            st.session_state.usuario = usuario_input
            st.session_state.tipo = usuario_logado["tipo"]
            st.rerun() if hasattr(st, "rerun") else st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# VARIÁVEIS DE SESSÃO
usuario_input = st.session_state.usuario
tipo_usuario = st.session_state.tipo

# Carregar escolas com limpeza de espaços
try:
    escolas_df = pd.read_excel("etcs.xlsx")
    escolas_df = escolas_df.astype(str).apply(lambda x: x.str.strip())
except Exception as e:
    st.error(f"Erro ao carregar etcs.xlsx: {e}")
    st.stop()

# Banco de dados
import os
db_path = os.path.abspath("etec.db")
st.write(f"📁 Banco de dados em: {db_path}")
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
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
""")
conn.commit()
            # st.write(f"[LOG] ...")  # Removido do ambiente de produção

# Interface principal
st.markdown(f"""
    <div style='text-align: center;'>
        <img src='data:image/png;base64,{logo_base64}' width='400'>
        <h1>Cadastro de Coordenadores - Vestibulinho ETEC 2025.2</h1>
    </div>
""", unsafe_allow_html=True)

# AÇÕES DO ADMINISTRADOR NA SIDEBAR
st.sidebar.markdown("## 📋 Ações Administrativas")
if tipo_usuario == "admin":
    if st.sidebar.button("🧨 Zerar todos os cadastros"):
        st.sidebar.warning("⚠️ Esta ação apagará todos os cadastros do sistema. Confirme abaixo.")
        if st.sidebar.button("❌ Confirmar exclusão total"):
            with open("exclusao_total.log", "a") as log:
                log.write(f"Exclusão total realizada por {usuario_input} (tipo: {tipo_usuario})
")
            cursor.execute("DELETE FROM coordenadores"
            conn.commit()
            st.sidebar.success("Todos os cadastros foram apagados.")
            df_vazio = pd.read_sql_query("SELECT * FROM coordenadores", conn)
            st.sidebar.dataframe(df_vazio)
            st.rerun()
    acao = st.sidebar.radio("Escolha uma ação:", ["Visualizar Cadastros", "Adicionar Novo", "Editar Cadastro", "Excluir Cadastro"], key="acao_admin")
else:
    acao = "Adicionar Novo"

if st.sidebar.button("🚪 Sair"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# AÇÃO: VISUALIZAR TABELA
if acao == "Visualizar Cadastros":
    st.subheader("📊 Tabela de Cadastros")
    df_admin = pd.read_sql_query("SELECT * FROM coordenadores", conn)
    st.dataframe(df_admin)
    st.sidebar.download_button("📅 Exportar CSV", df_admin.to_csv(index=False), "cadastros.csv", "text/csv")
    with open(db_path, "rb") as db_file:
        st.sidebar.download_button("🧾 Baixar Banco de Dados", db_file, file_name="etec.db", mime="application/octet-stream")

# AÇÃO: EDITAR CADASTRO
if acao == "Editar Cadastro":
    st.subheader("✏️ Editar Cadastro Existente")
    unidades_disponiveis = pd.read_sql_query("SELECT DISTINCT unidade FROM coordenadores ORDER BY unidade", conn)['unidade'].tolist()
    unidade_filtrada = st.selectbox("Selecione a Unidade para editar registros:", unidades_disponiveis)

    query = f"SELECT id, nome, cpf FROM coordenadores WHERE unidade = '{unidade_filtrada}'"

    cadastros = pd.read_sql_query(query, conn)
    filtro_busca = st.text_input("Buscar por nome ou CPF:").strip().lower()
    if filtro_busca:
        cadastros = cadastros[cadastros.apply(lambda row: filtro_busca in row['nome'].lower() or filtro_busca in row['cpf'], axis=1)]

    cadastros['display'] = cadastros['nome'] + " - CPF: " + cadastros['cpf']
    selecionado = st.selectbox("Selecione um cadastro para editar:", cadastros['display'])

    if selecionado:
        id_sel = cadastros[cadastros['display'] == selecionado]['id'].values[0]
        dados = pd.read_sql_query(f"SELECT * FROM coordenadores WHERE id = {id_sel}", conn).iloc[0]

        with st.form("form_edicao"):
            nome = st.text_input("Nome completo", value=dados["nome"])
            telefone = st.text_input("Telefone de contato", value=dados["telefone"])
            cpf = st.text_input("CPF", value=dados["cpf"])
            banco = st.text_input("Banco", value=dados["banco"])
            agencia = st.text_input("Agência", value=dados["agencia"])
            conta = st.text_input("Conta (com dígito)", value=dados["conta"])
            tipo_chave = st.radio("Tipo de chave Pix", ["CPF", "Telefone", "E-mail", "Aleatória"], index=["CPF", "Telefone", "E-mail", "Aleatória"].index(dados["tipo_chave"]))
            chave_pix = st.text_input("Chave Pix", value=dados["chave_pix"])
            centro_distribuicao = st.radio("Sua unidade gostaria de ser Centro de Distribuição?", ["Sim", "Não"], index=["Sim", "Não"].index(dados["centro_distribuicao"]))
            coordenador_prova = st.radio("Você será Coordenador de Local de Prova?", ["Sim", "Não"], index=["Sim", "Não"].index(dados["coordenador_prova"]))
            divulgacao_lista = [d.strip() for d in dados["divulgacao"].split(",")] if dados["divulgacao"] else []
            divulgacao = st.multiselect("Meio(s) de Divulgação mais efetivo(s) para o Vestibulinho", [
                "Tráfego Pago", "Propaganda em TV", "Distribuição Física de Panfletos e Flyers",
                "Cartazes/Banners em Locais de Grande Circulação", "Busdoor/Outdoor", "Outros"], default=divulgacao_lista)
            outros_meios = st.text_input("Quais?", value=dados["outros_meios"])
            observacoes = st.text_area("Observações e Sugestões", value=dados["observacoes"])

            salvar = st.form_submit_button("💾 Atualizar Cadastro")
            if salvar:
                cursor.execute("""
                    UPDATE coordenadores SET
                        nome = ?, telefone = ?, cpf = ?, banco = ?, agencia = ?, conta = ?,
                        tipo_chave = ?, chave_pix = ?, centro_distribuicao = ?, coordenador_prova = ?,
                        divulgacao = ?, outros_meios = ?, observacoes = ?
                    WHERE id = ?
                """, (
                    nome, telefone, cpf, banco, agencia, conta, tipo_chave, chave_pix,
                    centro_distribuicao, coordenador_prova, ", ".join(divulgacao), outros_meios,
                    observacoes, id_sel
                ))
                conn.commit()
                st.success("Cadastro atualizado com sucesso!")
                st.rerun()

# AÇÃO: EXCLUIR CADASTRO
if acao == "Excluir Cadastro":
    st.subheader("🗑️ Excluir Cadastro")
    unidades_disponiveis = pd.read_sql_query("SELECT DISTINCT unidade FROM coordenadores ORDER BY unidade", conn)['unidade'].tolist()
    unidade_filtrada = st.selectbox("Selecione a Unidade para excluir registros:", unidades_disponiveis)

    query = f"SELECT id, nome, cpf FROM coordenadores WHERE unidade = '{unidade_filtrada}'"

    cadastros = pd.read_sql_query(query, conn)
    filtro_busca = st.text_input("Buscar por nome ou CPF:").strip().lower()
    if filtro_busca:
        cadastros = cadastros[cadastros.apply(lambda row: filtro_busca in row['nome'].lower() or filtro_busca in row['cpf'], axis=1)]

    cadastros['display'] = cadastros['nome'] + " - CPF: " + cadastros['cpf']
    selecionado = st.selectbox("Selecione um cadastro para excluir:", cadastros['display'])

    if selecionado:
        id_sel = cadastros[cadastros['display'] == selecionado]['id'].values[0]
        with st.form("form_excluir"):
            st.warning("⚠️ Esta ação é irreversível. Tem certeza que deseja excluir este cadastro?")
            confirmar = st.form_submit_button("❌ Confirmar Exclusão")
            if confirmar:
                cursor.execute("DELETE FROM coordenadores WHERE id = ?", (id_sel,))
                conn.commit()
                st.success("Cadastro excluído com sucesso!")
                st.rerun()

# AÇÃO: ADICIONAR NOVO
if acao == "Adicionar Novo":
    st.subheader("Informações da Unidade Escolar")
    regioes = ["-- selecione --"] + sorted(escolas_df['Região Administrativa'].unique())
    regiao_sel = st.selectbox("Região Administrativa", regioes)

    if regiao_sel != "-- selecione --":
        df_municipios = escolas_df[escolas_df['Região Administrativa'] == regiao_sel]
        municipios = ["-- selecione --"] + sorted(df_municipios['Município'].unique())
        municipio_sel = st.selectbox("Município", municipios)

        if municipio_sel != "-- selecione --":
            df_unidades = df_municipios[df_municipios['Município'] == municipio_sel]
            unidades = ["-- selecione --"] + sorted(df_unidades['Unidade'].unique())
            unidade_sel = st.selectbox("Unidade (ETEC)", unidades)

            if unidade_sel != "-- selecione --":
                endereco = df_unidades[df_unidades['Unidade'] == unidade_sel]['Endereço'].values[0]
                st.text_input("Endereço completo da Unidade", value=endereco, disabled=True)

                with st.form("form"):
                    st.subheader("Dados Pessoais")
                    nome = st.text_input("Nome completo")
                    telefone = st.text_input("Telefone de contato", max_chars=15)
                    cpf = st.text_input("CPF", max_chars=14)

                    st.subheader("Dados Bancários")
                    banco = st.text_input("Banco")
                    agencia = st.text_input("Agência")
                    conta = st.text_input("Conta (com dígito)")
                    tipo_chave = st.radio("Tipo de chave Pix", ["CPF", "Telefone", "E-mail", "Aleatória"])
                    chave_pix = st.text_input("Chave Pix")

                    st.subheader("Funções no Processo Seletivo")
                    centro_distribuicao = st.radio("Sua unidade gostaria de ser Centro de Distribuição?", ["Sim", "Não"])
                    coordenador_prova = st.radio("Você será Coordenador de Local de Prova?", ["Sim", "Não"])

                    divulgacao = st.multiselect("Meio(s) de Divulgação mais efetivo(s) para o Vestibulinho", [
                        "Tráfego Pago", "Propaganda em TV", "Distribuição Física de Panfletos e Flyers",
                        "Cartazes/Banners em Locais de Grande Circulação", "Busdoor/Outdoor", "Outros"], max_selections=2)

                    outros_meios = ""
                    if "Outros" in divulgacao:
                        outros_meios = st.text_input("Quais?")

                    observacoes = st.text_area("Observações e Sugestões")

                    submitted = st.form_submit_button("Salvar Cadastro")
                    if submitted:
                        if not (re.fullmatch(r'\d{11}', cpf.replace('.', '').replace('-', '')) and re.fullmatch(r'\d{10,11}', telefone.replace('(', '').replace(')', '').replace('-', '').replace(' ', ''))):
                            st.error("CPF ou telefone inválido. Verifique e tente novamente.")
                        else:
                            cursor.execute("""
                                INSERT INTO coordenadores (
                                    nome, telefone, cpf, banco, agencia, conta,
                                    tipo_chave, chave_pix, unidade, endereco,
                                    centro_distribuicao, coordenador_prova, divulgacao,
                                    outros_meios, observacoes
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                nome, telefone, cpf, banco, agencia, conta, tipo_chave, chave_pix,
                                unidade_sel, endereco, centro_distribuicao, coordenador_prova,
                                ", ".join(divulgacao), outros_meios, observacoes
                            ))
                            conn.commit()
                            st.write(f"[LOG] Novo cadastro salvo: {nome} - CPF: {cpf}")
                            st.success("Cadastro realizado com sucesso!")
                            st.markdown("""
                                <div style='text-align: center; margin-top: 2em;'>
                                    <h3 style='color: green;'>✅ Tudo certo!</h3>
                                    <p>Seu cadastro foi registrado com sucesso no sistema.</p>
                                </div>
                            """, unsafe_allow_html=True)
                            import time
                            time.sleep(5)
                            st.rerun()
