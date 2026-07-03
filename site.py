import streamlit as st
from datetime import datetime, date
import sqlite3
import time

st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")
st.write("Sistema permanente ativo. Aguardando comandos do cozinheiro **Victor**.")

conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()

# Garantir estrutura
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL, peso REAL, unidade TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY AUTOINCREMENT, item_nome TEXT, item_marca TEXT UNIQUE)")
conn.commit()

# Funções
def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4], "quantidade": l[5], "peso": l[6], "unidade": l[7]} for l in cursor.fetchall()]

def carregar_historico_marcas():
    cursor.execute("SELECT DISTINCT item_marca FROM historico WHERE item_marca IS NOT NULL")
    return [l[0] for l in cursor.fetchall()]

if "backup" not in st.session_state: st.session_state.backup = None

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📥 Cadastrar Produto")
    nome = st.text_input("Nome do Produto")
    marcas = carregar_historico_marcas()
    marca = st.selectbox("Marca", [""] + marcas)
    local = st.selectbox("Local", ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"])
    qtd = st.number_input("Quantidade", value=1.0)
    unid = st.selectbox("Unidade", ["Kg", "g", "L", "mL"])
    peso = st.number_input("Peso/Volume", value=0.0)
    val = st.date_input("Validade")

    if st.button("🚀 Adicionar ao Estoque"):
        cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", (nome, marca, local, val.strftime("%Y-%m-%d"), qtd, peso, unid))
        if marca: cursor.execute("INSERT OR IGNORE INTO historico (item_marca) VALUES (?)", (marca,))
        conn.commit()
        st.rerun()

with col2:
    st.header("🚨 Estoque Atual")
    produtos = carregar_produtos()
    
    if produtos:
        if st.button("🗑️ Limpar Todo o Estoque"):
            st.session_state.backup = produtos
            cursor.execute("DELETE FROM produtos")
            conn.commit()
            st.rerun()
    
    if st.session_state.backup and st.button("🔄 Desfazer Limpeza"):
        for p in st.session_state.backup:
            cursor.execute("INSERT INTO produtos VALUES (?,?,?,?,?,?,?,?)", (None, p['nome'], p['local'], p['validade'], p['marca'], p['quantidade'], p['peso'], p['unidade']))
        conn.commit()
        st.session_state.backup = None
        st.rerun()

    for item in produtos:
        dias = (item["validade"] - date.today()).days
        cor = "#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a")
        
        with st.container():
            st.markdown(f"""
            <div style="border-left: 6px solid {cor}; padding: 15px; background: #f8fafc; margin-bottom: 10px; border-radius: 5px;">
                <b>{item['nome']}</b> | Marca: {item['marca']}<br>
                📦 {item['quantidade']:.0f} x {item['peso']}{item['unidade']} | 📍 {item['local']}<br>
                📅 Validade: {item['validade'].strftime('%d/%m/%Y')} ({dias} dias)
            </div>
            """, unsafe_allow_html=True)
            if st.button("❌ Excluir Produto", key=f"del_{item['id']}"):
                cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
                conn.commit()
                st.rerun()
