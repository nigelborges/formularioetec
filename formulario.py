import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Sistema Escolar - Acesso", layout="centered")

# Acesso direto como usuário comum
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = {'id': -1, 'nome': 'visitante', 'nivel': 'cadastrador'}

# Botão para login como admin
with st.sidebar:
    if st.button("🔐 Logar como Administrador"):
        with st.form("login_admin"):
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if usuario_input == 'admin' and senha_input == '1234':
                    st.session_state['usuario'] = {'id': 0, 'nome': 'admin', 'nivel': 'admin'}
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

DB_FILE = 'escolas.db'
SAVE_FILE = 'escolas_salvas.csv'

# Criar banco de dados e tabelas se não existirem
conn = sqlite3.connect(DB_FILE)
conn.execute("""
    CREATE TABLE IF NOT EXISTS escolas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        endereco TEXT NOT NULL,
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

def carregar_escolas():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    usuario = st.session_state['usuario']
    if usuario['nivel'] == 'admin':
        cursor.execute("SELECT id, nome, endereco, usuario_id FROM escolas")
    else:
        cursor.execute("SELECT id, nome, endereco, usuario_id FROM escolas WHERE usuario_id = ?", (usuario['id'],))
    dados = cursor.fetchall()
    conn.close()
    return pd.DataFrame(dados, columns=['id', 'nome', 'endereco', 'usuario_id'])

def carregar_salas_por_escola(escola_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT nome_sala, bloco, andar, candidatos_sala FROM salas WHERE escola_id = ?", (escola_id,))
    dados = cursor.fetchall()
    conn.close()
    return pd.DataFrame(dados, columns=['nome_sala', 'bloco', 'andar', 'candidatos_sala'])

def salvar_escola_banco(nome, endereco, salas, editar_id=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    usuario_id = st.session_state['usuario']['id']

    if editar_id is not None:
        cursor.execute("UPDATE escolas SET nome = ?, endereco = ? WHERE id = ?", (nome, endereco, editar_id))
        cursor.execute("DELETE FROM salas WHERE escola_id = ?", (editar_id,))
        escola_id = editar_id
    else:
        cursor.execute("INSERT INTO escolas (nome, endereco, usuario_id) VALUES (?, ?, ?)", (nome, endereco, usuario_id))
        escola_id = cursor.lastrowid

    for sala in salas:
        cursor.execute("""
            INSERT INTO salas (escola_id, nome_sala, bloco, andar, candidatos_sala)
            VALUES (?, ?, ?, ?, ?)
        """, (escola_id, sala['nome_sala'], sala['bloco'], sala['andar'], sala['candidatos_sala']))

    conn.commit()
    conn.close()

def excluir_escola(escola_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM salas WHERE escola_id = ?", (escola_id,))
    cursor.execute("DELETE FROM escolas WHERE id = ?", (escola_id,))
    conn.commit()
    conn.close()

def exportar_dados_geral():
    usuario = st.session_state['usuario']
    df_escolas = carregar_escolas()
    if usuario['nivel'] != 'admin':
        df_escolas = df_escolas[df_escolas['usuario_id'] == usuario['id']]

    todos = []
    for _, escola in df_escolas.iterrows():
        df_salas = carregar_salas_por_escola(escola['id'])
        id_sala_counter = 1
        sala_ids = {}
        for i, sala in df_salas.iterrows():
            nome = sala['nome_sala']
            if nome not in sala_ids:
                sala_ids[nome] = id_sala_counter
                id_sala_counter += 1
            id_sala = sala_ids[nome]
            for ordem in range(1, sala['candidatos_sala'] + 1):
                todos.append({
                    'ID Escola': escola['id'],
                    'Nome Escola': escola['nome'],
                    'Endereco': escola['endereco'],
                    'ID Sala': id_sala,
                    'Nome da Sala': sala['nome_sala'],
                    'Bloco': sala['bloco'],
                    'Andar': sala['andar'],
                    'Ordem da Sala': i + 1,
                    'Numero de Salas': len(df_salas),
                    'Ordem do Candidato': ordem
                })
    return pd.DataFrame(todos)

def visualizar():
    st.title("📋 Escolas Cadastradas")
    st.divider()

    filtro_nome = st.text_input("🔎 Filtrar por nome da escola")
    filtro_endereco = st.text_input("📍 Filtrar por endereço")

    df_escolas = carregar_escolas()
    if filtro_nome:
        df_escolas = df_escolas[df_escolas['nome'].str.contains(filtro_nome, case=False, na=False)]
    if filtro_endereco:
        df_escolas = df_escolas[df_escolas['endereco'].str.contains(filtro_endereco, case=False, na=False)]

    if df_escolas.empty:
        st.info("Nenhuma escola encontrada com os filtros atuais.")
        return

    for _, escola in df_escolas.iterrows():
        with st.expander(f"🏫 {escola['nome']} - {escola['endereco']}"):
            st.subheader(f"📄 Salas da escola {escola['nome']}")
            st.caption(f"Endereço: {escola['endereco']}")
            st.markdown("---")
            df_salas = carregar_salas_por_escola(escola['id'])
            if df_salas.empty:
                st.write("Nenhuma sala cadastrada.")
            else:
                df_salas_visual = df_salas.copy()
                id_sala_counter = 1
                sala_ids = {}
                id_salas = []
                for _, sala in df_salas_visual.iterrows():
                    nome = sala['nome_sala']
                    if nome not in sala_ids:
                        sala_ids[nome] = id_sala_counter
                        id_sala_counter += 1
                    id_salas.append(sala_ids[nome])
                df_salas_visual.insert(0, "ID Sala", id_salas)
                df_salas_visual.insert(0, "ID Escola", escola['id'])
                df_salas_visual.insert(1, "Nome Escola", escola['nome'])
                df_salas_visual.insert(1, "Endereco", escola['endereco'])
                st.dataframe(df_salas_visual)

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button(f"✏️ Editar", key=f"editar_{escola['id']}", use_container_width=True):
                    st.session_state['modo_edicao'] = True
                    st.session_state['escola_em_edicao'] = escola['id']
                    st.session_state['pagina_atual'] = "Cadastrar Escola"
                    st.rerun()
            with col2:
                if st.button(f"🗑️ Excluir", key=f"excluir_{escola['id']}", use_container_width=True):
                    excluir_escola(escola['id'])
                    st.success("Escola excluída.")
                    st.rerun()
            with col3:
                if st.session_state['usuario']['nivel'] == 'admin':
                    if st.button(f"📁 Exportar CSV", key=f"botao_exportar_{escola['id']}", use_container_width=True):
                        df_exportar = exportar_dados_geral()
                        st.download_button(
                            "⬇️ Baixar CSV",
                            df_exportar.to_csv(index=False).encode('utf-8'),
                            file_name=f"escola_{escola['id']}.csv",
                            key=f"download_{escola['id']}"
                        )
