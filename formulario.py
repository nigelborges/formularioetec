import streamlit as st
import sqlite3
import re
import pandas as pd
from PIL import Image
import base64
from io import BytesIO

# ==== USUÁRIOS E SENHAS ====
usuarios = {
    "admin": {"senha": "admin2025", "tipo": "admin"},
    "usuario1": {"senha": "123", "tipo": "comum"},
}

# LOGIN CENTRALIZADO
if "usuario" not in st.session_state:
    st.markdown("""
        <div style='text-align: center;'>
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
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
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

# Logo e título centralizados
def get_image_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode()

logo = Image.open("idecan.png")
logo_base64 = get_image_base64(logo)

st.markdown(f"""
    <div style='text-align: center;'>
        <img src='data:image/png;base64,{logo_base64}' width='400'>
        <h1>Cadastro de Coordenadores - Vestibulinho ETEC 2025.2</h1>
    </div>
""", unsafe_allow_html=True)

# AÇÕES DO ADMINISTRADOR NA SIDEBAR
st.sidebar.markdown("## 📋 Ações Administrativas")
if tipo_usuario == "admin":
    acao = acao = st.sidebar.radio("Escolha uma ação:", ["Visualizar Cadastros", "Adicionar Novo", "Editar Cadastro", "Excluir Cadastro"], key="acao_admin")
if st.sidebar.button("🚪 Sair"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
else:
    acao = "Adicionar Novo"

# AÇÃO: VISUALIZAR TABELA
if acao == "Visualizar Cadastros":
    st.subheader("📊 Tabela de Cadastros")
    df_admin = pd.read_sql_query("SELECT id, nome, cpf, telefone, unidade FROM coordenadores", conn)
    st.dataframe(df_admin)
    st.sidebar.download_button("📥 Exportar CSV", df_admin.to_csv(index=False), "cadastros.csv", "text/csv")

# AÇÃO: EDITAR CADASTRO
elif acao == "Editar Cadastro" and tipo_usuario == "admin":
    df_edit = pd.read_sql_query("SELECT * FROM coordenadores", conn)
    if not df_edit.empty:
        selecionado = st.selectbox("Escolha o cadastro para editar:", df_edit['unidade'].tolist())
        dados = df_edit[df_edit['unidade'] == selecionado].iloc[0]

        with st.form("form_edit"):
            st.subheader("Editar Cadastro da Unidade")
            nome = st.text_input("Nome completo", value=dados["nome"])
            telefone = st.text_input("Telefone de contato", value=dados["telefone"])
            cpf = st.text_input("CPF", value=dados["cpf"])
            banco = st.text_input("Banco", value=dados["banco"])
            agencia = st.text_input("Agência", value=dados["agencia"])
            conta = st.text_input("Conta", value=dados["conta"])
            tipo_chave = st.selectbox("Tipo de chave Pix", ["CPF", "Telefone", "E-mail", "Aleatória"], index=["CPF", "Telefone", "E-mail", "Aleatória"].index(dados["tipo_chave"]))
            chave_pix = st.text_input("Chave Pix", value=dados["chave_pix"])
            centro_distribuicao = st.radio("Centro de Distribuição?", ["Sim", "Não"], index=["Sim", "Não"].index(dados["centro_distribuicao"]))
            coordenador_prova = st.radio("Coordenador de Prova?", ["Sim", "Não"], index=["Sim", "Não"].index(dados["coordenador_prova"]))
            divulgacao = st.multiselect("Meios de Divulgação", ["Tráfego Pago", "Propaganda em TV", "Distribuição Física de Panfletos e Flyers", "Cartazes/Banners em Locais de Grande Circulação", "Busdoor/Outdoor", "Outros"], default=dados["divulgacao"].split(", "))
            outros_meios = st.text_input("Outros Meios", value=dados["outros_meios"])
            observacoes = st.text_area("Observações", value=dados["observacoes"])

            submit = st.form_submit_button("Salvar Alterações")

            if submit:
                cursor.execute("""
                    UPDATE coordenadores SET
                        nome=?, telefone=?, cpf=?, banco=?, agencia=?, conta=?, tipo_chave=?, chave_pix=?,
                        centro_distribuicao=?, coordenador_prova=?, divulgacao=?, outros_meios=?, observacoes=?
                    WHERE id=?
                """, (nome, telefone, cpf, banco, agencia, conta, tipo_chave, chave_pix,
                      centro_distribuicao, coordenador_prova, ", ".join(divulgacao), outros_meios, observacoes, dados["id"]))
                conn.commit()
                st.success("Cadastro atualizado com sucesso!")
                st.rerun()

# AÇÃO: EXCLUIR CADASTRO
elif acao == "Excluir Cadastro" and tipo_usuario == "admin":
    st.subheader("🗑️ Excluir Cadastro de ETEC")
    df_cadastrados = pd.read_sql_query("SELECT id, unidade FROM coordenadores", conn)
    etecs_cadastradas = df_cadastrados['unidade'].unique().tolist()
    if etecs_cadastradas:
        unidade_excluir = st.selectbox("Unidade cadastrada para excluir", etecs_cadastradas)
        confirmar = st.checkbox("Confirmar exclusão")
        if st.button("Excluir cadastro") and confirmar:
            cursor.execute("DELETE FROM coordenadores WHERE unidade = ?", (unidade_excluir,))
            conn.commit()
            st.success(f"Cadastro da unidade '{unidade_excluir}' foi removido.")
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
    else:
        st.info("Nenhuma unidade cadastrada no momento.")

# AÇÃO: ADICIONAR NOVO (ou usuário comum)
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

                    submitted = st.form_submit_button("Salvar Cadastro")

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
                            if st.button("Novo Cadastro"):
                                st.rerun()
        st.markdown("""
            <div style='text-align: center; margin-top: 2em;'>
                <h3 style='color: green;'>✅ Tudo certo!</h3>
                <p>Seu cadastro foi registrado com sucesso no sistema.</p>
            </div>
        """, unsafe_allow_html=True)
