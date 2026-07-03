import streamlit as st
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")

conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL, peso REAL, unidade TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_produtos (nome TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_marcas (nome TEXT UNIQUE)")
conn.commit()

# ... (funções carregar_produtos e para_float permanecem iguais) ...

def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1] or "", "local": l[2] or "", "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4] or "", "quantidade": l[5] or 0.0, "peso": l[6] or 0.0, "unidade": l[7] or ""} for l in cursor.fetchall()]

if "edit_data" not in st.session_state: st.session_state.edit_data = None

col1, col2 = st.columns([1, 2])

with col1:
    is_editing = st.session_state.edit_data is not None
    st.header("✏️ Editar" if is_editing else "📥 Cadastrar")
    d = st.session_state.edit_data if is_editing else {}

    nome_final = st.text_input("Nome do Produto", value=d.get("nome", ""))
    marca_final = st.text_input("Marca", value=d.get("marca", ""))
    # ... (restante do form de cadastro) ...
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais, index=locais.index(d["local"]) if is_editing and d.get("local") in locais else 0)
    qtd_f = st.number_input("Quantidade", value=float(d.get("quantidade", 1.0)))
    unidades = ["Kg", "g", "L", "mL"]
    unid_f = st.selectbox("Unidade", unidades, index=unidades.index(d.get("unidade", "Kg")) if is_editing and d.get("unidade") in unidades else 0)
    peso_f = st.number_input("Peso/Volume", value=float(d.get("peso", 0.0)))
    data_f = st.date_input("Validade", value=d.get("validade", date.today()))

    if is_editing:
        c1, c2 = st.columns(2)
        if c1.button("💾 Atualizar"):
            cursor.execute("UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=?, peso=?, unidade=? WHERE id=?", (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f, d["id"]))
            conn.commit(); st.session_state.edit_data = None; st.rerun()
        if c2.button("❌ Cancelar"): st.session_state.edit_data = None; st.rerun()
    else:
        if st.button("🚀 Salvar"):
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f))
            cursor.execute("INSERT OR IGNORE INTO historico_produtos (nome) VALUES (?)", (nome_final,))
            cursor
