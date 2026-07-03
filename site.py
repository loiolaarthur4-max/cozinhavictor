import streamlit as st
import sqlite3
from datetime import datetime, date

st.set_page_config(page_title="Controle Cozinha", layout="wide")

# Conexão
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL)")
conn.commit()

st.title("🍳 Sistema de Controle")

# Sidebar com Câmera Nativa
with st.sidebar:
    st.header("📸 Scanner")
    # O camera_input é o componente mais estável do Streamlit
    img_file = st.camera_input("Tire foto do código")
    
    st.header("📥 Cadastrar")
    # Se uma foto for tirada, você pode nomeá-la ou apenas usar como ref
    nome_f = st.text_input("Nome do Produto")
    marca_f = st.text_input("Marca")
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais)
    qtd_f = st.number_input("Quantidade", value=1.0)
    data_f = st.date_input("Validade")

    if st.button("🚀 Salvar"):
        cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade) VALUES (?,?,?,?,?)", 
                       (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f))
        conn.commit()
        st.success("Salvo!")
        st.rerun()

# Conteúdo Principal
st.header("🚨 Estoque")
produtos = [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4]} for l in cursor.execute("SELECT * FROM produtos").fetchall()]

for item in produtos:
    dias = (item["validade"] - date.today()).days
    cor = "#ef4444" if dias <= 3 else "#16a34a"
    c1, c2 = st.columns([5, 1])
    c1.markdown(f'<div style="background:{cor}; color:white; padding:10px; border-radius:5px;">{item["nome"]} - {item["marca"]} ({dias} dias)</div>', unsafe_allow_html=True)
    if c2.button("❌", key=f"del_{item['id']}"):
        cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
        conn.commit()
        st.rerun()
