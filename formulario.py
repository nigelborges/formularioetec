import streamlit as st
import sqlite3
import re
import pandas as pd
from PIL import Image
import base64
from io import BytesIO
from streamlit.components.v1 import html as st_html

st_html("""
<script>
function applyCpfMask(input){
  input.addEventListener('input', function(){
    let value = input.value.replace(/\D/g, '').slice(0, 11);
    value = value.replace(/(\d{3})(\d)/, '$1.$2')
                 .replace(/(\d{3})(\d)/, '$1.$2')
                 .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    input.value = value;
  });
}
function applyPhoneMask(input){
  input.addEventListener('input', function(){
    let value = input.value.replace(/\D/g, '').slice(0, 11);
    if (value.length > 6) {
      value = value.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
    } else if (value.length > 2) {
      value = value.replace(/(\d{2})(\d{0,5})/, '($1) $2');
    } else {
      value = value.replace(/(\d{0,2})/, '($1');
    }
    input.value = value;
  });
}
document.querySelectorAll('input[placeholder="000.000.000-00"]').forEach(applyCpfMask);
document.querySelectorAll('input[placeholder="(00) 00000-0000"]').forEach(applyPhoneMask);
</script>
""", height=0)

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
