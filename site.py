import streamlit as st
from datetime import datetime, date
import sqlite3

# Configuração da página
st.set_page_config(page_title="Controle de Validade - Cozinha", page_icon="🍳", layout="wide")

st.title("🍳 Sistema de Controle da Cozinha")
st.write("Sistema permanente ativo. Aguardando comandos do cozinheiro **Victor**.")

conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()

# Tabelas e Upgrades
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT)")
for col, tipo in [("marca", "TEXT"), ("quantidade", "REAL DEFAULT 1.0"), ("peso", "REAL DEFAULT 0.0"), ("unidade", "TEXT DEFAULT 'Kg'")]:
    try: cursor.execute(f"ALTER TABLE produtos ADD COLUMN {col} {tipo}")
    except: pass
conn.commit()

# FUNÇÃO CARREGAR ESTOQUE
def carregar_produtos():
    cursor.execute("SELECT id, nome, marca, local, validade, quantidade, peso, unidade FROM produtos")
    return [{
        "id": l[0], "nome": l[1], "marca": l[2] or "", "local": l[3],
        "validade": datetime.strptime(l[4], "%Y-%m-%d").date(),
        "quantidade": l[5], "peso": l[6], "unidade": l[7]
    } for l in cursor.fetchall()]

# Estado da sessão
if "id_edicao" not in st.session_state: st.session_state.id_edicao = None
if "valores_edicao" not in st.session_state: st.session_state.valores_edicao = {}

col1, col2 = st.columns([1.1, 1.7])

with col1:
    if st.session_state.id_edicao is not None:
        st.header("✏️ Editar Produto")
        val = st.session_state.valores_edicao
    else:
        st.header("📥 Cadastrar Novo Produto")
        val = {"nome": "", "marca": "", "local": "Geladeira da Cozinha", "quantidade": 1.0, "unidade": "Kg", "peso": 0.0, "validade": date.today()}

    # Formulário
    nome_f = st.text_input("Nome do Produto:", value=val["nome"])
    marca_f = st.text_input("Marca:", value=val["marca"])
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local:", locais, index=locais.index(val["local"]) if val["local"] in locais else 0)
    qtd_f = st.number_input("Quantidade:", min_value=1.0, value=float(val["quantidade"]))
    unid_f = st.radio("Métrica:", ["Kg", "g", "L", "mL"], index=["Kg", "g", "L", "mL"].index(val["unidade"]) if val["unidade"] in ["Kg", "g", "L", "mL"] else 0, horizontal=True)
    peso_f = st.number_input("Volume/Peso:", value=float(val["peso"]))
    data_f = st.date_input("Validade:", value=val["validade"])

    if st.session_state.id_edicao:
        c1, c2 = st.columns(2)
        if c1.button("💾 Atualizar"):
            cursor.execute("UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=?, peso=?, unidade=? WHERE id=?", (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f, st.session_state.id_edicao))
            conn.commit()
            st.session_state.id_edicao = None
            st.rerun()
        if c2.button("❌ Cancelar"):
            st.session_state.id_edicao = None
            st.rerun()
    else:
        if st.button("🚀 Adicionar"):
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f))
            conn.commit()
            st.rerun()

with col2:
    st.header("🚨 Alarmes e Estoque Atual")
    produtos = carregar_produtos()
    for item in produtos:
        dias = (item["validade"] - date.today()).days
        status = "❌ VENCIDO!" if dias < 0 else (f"🚨 CRÍTICO: {dias} dias" if dias <= 3 else (f"⚠️ ATENÇÃO: {dias} dias" if dias <= 7 else f"✅ Seguro ({dias} dias)"))
        cor = "#ef4444" if dias < 0 or dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a")
        
        st.markdown(f"""
        <div style="border-left: 6px solid {cor}; padding: 10px; background: #f8fafc; margin-bottom: 10px;">
            <b>{item['nome']}</b> {f'({item['marca']})' if item['marca'] else ''}<br>
            📦 {item['quantidade']:.0f} Unid x {item['peso']:.2f} {item['unidade']}<br>
            📍 {item['local']} | 📅 {item['validade'].strftime('%d/%m/%Y')}<br>
            <b style="color: {cor}">{status}</b>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("✏️ Editar", key=f"e{item['id']}"):
            st.session_state.id_edicao = item['id']
            st.session_state.valores_edicao = item
            st.rerun()
        if c2.button("❌ Excluir", key=f"d{item['id']}"):
            cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
            conn.commit()
            st.rerun()
