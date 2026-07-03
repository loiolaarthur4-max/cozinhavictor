import streamlit as st
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")

# Conexão com banco
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL, peso REAL, unidade TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_produtos (nome TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_marcas (nome TEXT UNIQUE)")
conn.commit()

# Funções
def para_float(valor):
    try: return float(valor)
    except: return 0.0

# Sidebar
with st.sidebar:
    st.header("📷 Escanear")
    # Este botão abre a câmera nativa do seu Galaxy A13
    foto_codigo = st.camera_input("Tire uma foto do código de barras")
    
    st.markdown("---")
    
    st.header("📥 Cadastrar / Editar")
    nome_f = st.text_input("Nome do Produto")
    marca_f = st.text_input("Marca")
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais)
    qtd_f = st.number_input("Quantidade", value=1.0, step=1.0)
    data_f = st.date_input("Validade", value=date.today())

    if st.button("🚀 Salvar Produto"):
        cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso) VALUES (?,?,?,?,?,0)", 
                       (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f))
        conn.commit()
        st.success("Salvo!")
        st.rerun()

# Conteúdo Principal
st.header("🚨 Estoque")
cursor.execute("SELECT * FROM produtos")
produtos = [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4]} for l in cursor.fetchall()]

for item in produtos:
    dias = (item["validade"] - date.today()).days
    cor = "#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a")
    st.markdown(f'''<div style="padding: 10px; background-color: {cor}; color: white; border-radius: 8px; margin-bottom: 5px;">
        <b>{item["nome"]}</b> | <b>Local:</b> {item["local"]} | 📅 {dias} dias</div>''', unsafe_allow_html=True)
