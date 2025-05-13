import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Sistema Escolar", layout="centered")

# Inicializa sessão
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = {'id': -1, 'nome': 'visitante', 'nivel': 'cadastrador'}

# Login
with st.sidebar:
    st.header("Login")
    if st.button("🔐 Logar como Admin"):
        with st.form("form_login"):
            user = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if user == "admin" and senha == "1234":
                    st.session_state['usuario'] = {'id': 0, 'nome': 'admin', 'nivel': 'admin'}
                    st.success("Login realizado.")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

# Banco de dados
DB = 'escolas.db'
conn = sqlite3.connect(DB)
conn.execute("""
    CREATE TABLE IF NOT EXISTS escolas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        endereco TEXT,
        usuario_id INTEGER
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS salas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        escola_id INTEGER,
        nome_sala TEXT,
        bloco TEXT,
        andar TEXT,
        candidatos_sala INTEGER,
        FOREIGN KEY (escola_id) REFERENCES escolas(id)
    )
""")
conn.commit()
conn.close()

# Funções auxiliares
def carregar_escolas():
    conn = sqlite3.connect(DB)
    usuario = st.session_state['usuario']
    if usuario['nivel'] == 'admin':
        df = pd.read_sql("SELECT * FROM escolas", conn)
    else:
        df = pd.read_sql("SELECT * FROM escolas WHERE usuario_id = ?", conn, params=(usuario['id'],))
    conn.close()
    return df

def carregar_salas(escola_id):
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM salas WHERE escola_id = ?", conn, params=(escola_id,))
    conn.close()
    return df

def excluir_escola(escola_id):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM salas WHERE escola_id = ?", (escola_id,))
    conn.execute("DELETE FROM escolas WHERE id = ?", (escola_id,))
    conn.commit()
    conn.close()

def exportar_csv():
    usuario = st.session_state['usuario']
    df_escolas = carregar_escolas()
    todos = []

    for _, escola in df_escolas.iterrows():
        salas = carregar_salas(escola['id'])
        for _, sala in salas.iterrows():
            for ordem in range(1, sala['candidatos_sala'] + 1):
                todos.append({
                    'ID Escola': escola['id'],
                    'Nome Escola': escola['nome'],
                    'Endereço': escola['endereco'],
                    'Sala': sala['nome_sala'],
                    'Bloco': sala['bloco'],
                    'Andar': sala['andar'],
                    'Ordem do Candidato': ordem
                })
    return pd.DataFrame(todos)

# Interface principal
def visualizar():
    st.title("📚 Escolas Cadastradas")
    df = carregar_escolas()

    if df.empty:
        st.info("Nenhuma escola cadastrada.")
        return

    for _, escola in df.iterrows():
        with st.expander(f"{escola['nome']} - {escola['endereco']}"):
            salas = carregar_salas(escola['id'])
            if salas.empty:
                st.write("Nenhuma sala cadastrada.")
            else:
                st.dataframe(salas)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🗑️ Excluir", key=f"excluir_{escola['id']}"):
                    excluir_escola(escola['id'])
                    st.success("Escola excluída.")
                    st.rerun()
            with col2:
                if st.session_state['usuario']['nivel'] == 'admin':
                    df_export = exportar_csv()
                    st.download_button("⬇️ Exportar CSV", data=df_export.to_csv(index=False), file_name="escolas.csv")

def cadastrar():
    st.title("🏫 Cadastrar Nova Escola")
    nome = st.text_input("Nome da Escola")
    endereco = st.text_input("Endereço")

    num_salas = st.number_input("Número de salas", min_value=1, step=1)
    salas = []

    for i in range(num_salas):
        st.markdown(f"### Sala {i+1}")
        nome_sala = st.text_input(f"Nome da sala {i+1}", key=f"nome_{i}")
        bloco = st.text_input(f"Bloco da sala {i+1}", key=f"bloco_{i}")
        andar = st.text_input(f"Andar da sala {i+1}", key=f"andar_{i}")
        candidatos = st.number_input(f"Nº de candidatos na sala {i+1}", min_value=1, step=1, key=f"candidatos_{i}")
        salas.append((nome_sala, bloco, andar, candidatos))

    if st.button("💾 Salvar"):
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        usuario_id = st.session_state['usuario']['id']
        cursor.execute("INSERT INTO escolas (nome, endereco, usuario_id) VALUES (?, ?, ?)", (nome, endereco, usuario_id))
        escola_id = cursor.lastrowid

        for sala in salas:
            cursor.execute("""
                INSERT INTO salas (escola_id, nome_sala, bloco, andar, candidatos_sala)
                VALUES (?, ?, ?, ?, ?)""", (escola_id, *sala))

        conn.commit()
        conn.close()
        st.success("Escola cadastrada com sucesso!")
        st.rerun()

# Navegação
pagina = st.sidebar.radio("Menu", ["Visualizar", "Cadastrar"])
if pagina == "Visualizar":
    visualizar()
elif pagina == "Cadastrar":
    cadastrar()
