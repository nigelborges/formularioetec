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
    "admin": {"senha": "admin2025", "tipo": "admin"},
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
    df_admin = pd.read_sql_query("SELECT id, nome, cpf, telefone, unidade FROM coordenadores", conn)
    st.dataframe(df_admin)
    st.sidebar.download_button("📅 Exportar CSV", df_admin.to_csv(index=False), "cadastros.csv", "text/csv")

# AÇÃO: ADICIONAR NOVO
# (esta parte permanece igual)

# AÇÃO: EDITAR CADASTRO
if acao == "Editar Cadastro":
    st.subheader("✏️ Editar Cadastro Existente")
    cadastros = pd.read_sql_query("SELECT id, nome, cpf FROM coordenadores", conn)
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
            centro_distribuicao = st.radio("Centro de Distribuição?", ["Sim", "Não"], index=["Sim", "Não"].index(dados["centro_distribuicao"]))
            coordenador_prova = st.radio("Coordenador de Prova?", ["Sim", "Não"], index=["Sim", "Não"].index(dados["coordenador_prova"]))
            divulgacao_lista = [d.strip() for d in dados["divulgacao"].split(",")] if dados["divulgacao"] else []
            divulgacao = st.multiselect("Meios de Divulgação", ["Tráfego Pago", "Propaganda em TV", "Distribuição Física de Panfletos e Flyers", "Cartazes/Banners em Locais de Grande Circulação", "Busdoor/Outdoor", "Outros"], default=divulgacao_lista)
            outros_meios = st.text_input("Outros meios", value=dados["outros_meios"])
            observacoes = st.text_area("Observações", value=dados["observacoes"])
            atualizar = st.form_submit_button("Salvar alterações")
            if atualizar:
                cursor.execute("""
                    UPDATE coordenadores SET
                        nome=?, telefone=?, cpf=?, banco=?, agencia=?, conta=?, tipo_chave=?, chave_pix=?,
                        centro_distribuicao=?, coordenador_prova=?, divulgacao=?, outros_meios=?, observacoes=?
                    WHERE id=?
                """, (
                    nome, telefone, cpf, banco, agencia, conta, tipo_chave, chave_pix,
                    centro_distribuicao, coordenador_prova, ", ".join(divulgacao), outros_meios, observacoes,
                    id_sel
                ))
                conn.commit()
                st.success("Cadastro atualizado com sucesso!")
                st.experimental_rerun()

# AÇÃO: EXCLUIR CADASTRO
if acao == "Excluir Cadastro":
    st.subheader("🔌 Excluir Cadastro")
    cadastros = pd.read_sql_query("SELECT id, nome, cpf FROM coordenadores", conn)
    cadastros['display'] = cadastros['nome'] + " - CPF: " + cadastros['cpf']
    selecionado = st.selectbox("Selecione um cadastro para excluir:", cadastros['display'])
    if selecionado:
        id_sel = cadastros[cadastros['display'] == selecionado]['id'].values[0]
        confirmar = st.button("Confirmar exclusão")
        if confirmar:
            cursor.execute("DELETE FROM coordenadores WHERE id=?", (id_sel,))
            conn.commit()
            st.success("Cadastro excluído com sucesso!")
            st.experimental_rerun()
