import streamlit as st
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")

# Conexão
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL, peso REAL, unidade TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_produtos (nome TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_marcas (nome TEXT UNIQUE)")
conn.commit()

# --- FUNÇÕES ---
def para_float(valor):
    try: return float(valor)
    except: return 0.0

def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1] or "", "local": l[2] or "", "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4] or "", "quantidade": para_float(l[5]), "peso": para_float(l[6]), "unidade": l[7] or ""} for l in cursor.fetchall()]

def renderizar_card(item):
    dias = (item["validade"] - date.today()).days
    cor = "#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a")
    p = item['peso']
    peso_txt = f"{int(p) if p.is_integer() else p} {item['unidade']}"
    
    st.markdown(f'''<div style="padding: 10px; background-color: {cor}; color: white; border-radius: 8px; margin-bottom: 5px;">
        <b>{item["nome"]}</b> | <b>Marca:</b> {item["marca"]} | <b>Peso:</b> {peso_txt} | 📅 {dias} dias</div>''', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    if c1.button("✏️", key=f"e_{item['id']}"): st.session_state.edit_data = item; st.rerun()
    if c2.button("❌", key=f"d_{item['id']}"): 
        cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
        conn.commit(); st.rerun()

if "edit_data" not in st.session_state: st.session_state.edit_data = None

# --- SIDEBAR: CADASTRO ---
with st.sidebar:
    is_editing = st.session_state.edit_data is not None
    st.header("✏️ Editar" if is_editing else "📥 Cadastrar")
    d = st.session_state.edit_data if is_editing else {}
    
    nome_f = st.text_input("Nome do Produto", value=d.get("nome", ""))
    marca_f = st.text_input("Marca", value=d.get("marca", ""))
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais, index=locais.index(d.get("local", locais[0])) if is_editing and d.get("local") in locais else 0)
    qtd_f = st.number_input("Quantidade", value=para_float(d.get("quantidade", 1.0)), step=0.1)
    unidades = ["Kg", "g", "L", "mL"]
    unid_f = st.selectbox("Unidade", unidades, index=unidades.index(d.get("unidade", "Kg")) if is_editing and d.get("unidade") in unidades else 0)
    peso_f = st.number_input("Peso/Volume", value=para_float(d.get("peso", 0.0)), step=0.1)
    data_f = st.date_input("Validade", value=d.get("validade", date.today()))

    if is_editing:
        if st.button("💾 Atualizar"):
            cursor.execute("UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=?, peso=?, unidade=? WHERE id=?", (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f, d["id"]))
            conn.commit(); st.session_state.edit_data = None; st.rerun()
    else:
        if st.button("🚀 Salvar"):
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f))
            cursor.execute("INSERT OR IGNORE INTO historico_produtos (nome) VALUES (?)", (nome_f,))
            cursor.execute("INSERT OR IGNORE INTO historico_marcas (nome) VALUES (?)", (marca_f,))
            conn.commit(); st.rerun()

# --- ESTOQUE E PESQUISA ---
st.header("🚨 Estoque")
busca = st.text_input("🔍 Pesquisar produtos...", placeholder="Digite o nome do produto...")
produtos = carregar_produtos()

if busca:
    for item in [p for p in produtos if busca.lower() in p['nome'].lower()]:
        renderizar_card(item)
else:
    abas = st.tabs(locais + ["📜 Histórico"])
    for i, local in enumerate(locais):
        with abas[i]:
            for item in [p for p in produtos if p['local'] == local]:
                renderizar_card(item)
    
    with abas[-1]:
        c1, c2 = st.columns(2)
        with c1:
            st.write("### Produtos")
            cursor.execute("SELECT nome FROM historico_produtos")
            for r in cursor.fetchall(): st.code(r[0])
        with c2:
            st.write("### Marcas")
            cursor.execute("SELECT nome FROM historico_marcas")
            for r in cursor.fetchall(): st.code(r[0])
