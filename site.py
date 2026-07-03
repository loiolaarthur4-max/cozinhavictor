import streamlit as st
from datetime import datetime, date
import sqlite3
from streamlit_barcode_scanner import scan_barcode

# Configuração da página
st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")

# Conexão
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

def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1] or "", "local": l[2] or "", "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4] or "", "quantidade": para_float(l[5])} for l in cursor.fetchall()]

def renderizar_card(item):
    dias = (item["validade"] - date.today()).days
    cor = "#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a")
    
    st.markdown(f'''<div style="padding: 10px; background-color: {cor}; color: white; border-radius: 8px; margin-bottom: 5px;">
        <b>{item["nome"]}</b> | <b>Marca:</b> {item["marca"]} | <b>Local:</b> {item["local"]} | 📅 {dias} dias</div>''', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    if c1.button("✏️", key=f"e_{item['id']}"): 
        st.session_state.edit_data = item
        st.rerun()
    if c2.button("❌", key=f"d_{item['id']}"): 
        cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
        conn.commit()
        st.rerun()

# Estado de edição e barcode
if "edit_data" not in st.session_state: st.session_state.edit_data = None
if "scanned_barcode" not in st.session_state: st.session_state.scanned_barcode = None

# Sidebar
with st.sidebar:
    st.header("📷 Leitor de Código")
    if st.button("Abrir Câmera para Escanear"):
        scanned = scan_barcode()
        if scanned:
            st.session_state.scanned_barcode = scanned
            st.success(f"Código: {scanned}")

    is_editing = st.session_state.edit_data is not None
    st.header("✏️ Editar" if is_editing else "📥 Cadastrar")
    d = st.session_state.edit_data if is_editing else {}
    
    # Campo nome pré-preenchido se algo foi escaneado
    nome_input = f"Produto {st.session_state.scanned_barcode}" if st.session_state.scanned_barcode else d.get("nome", "")
    
    nome_f = st.text_input("Nome do Produto", value=nome_input)
    marca_f = st.text_input("Marca", value=d.get("marca", ""))
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais, index=locais.index(d.get("local", locais[0])) if is_editing and d.get("local") in locais else 0)
    qtd_f = st.number_input("Quantidade", value=para_float(d.get("quantidade", 1.0)), step=1.0)
    data_f = st.date_input("Validade", value=d.get("validade", date.today()))

    if is_editing:
        col1, col2 = st.columns(2)
        if col1.button("💾 Atualizar"):
            cursor.execute("UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=? WHERE id=?", (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, d["id"]))
            conn.commit(); st.session_state.edit_data = None; st.session_state.scanned_barcode = None; st.rerun()
        if col2.button("❌ Cancelar"):
            st.session_state.edit_data = None; st.session_state.scanned_barcode = None; st.rerun()
    else:
        if st.button("🚀 Salvar"):
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso) VALUES (?,?,?,?,?,0)", (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f))
            conn.commit(); st.session_state.scanned_barcode = None; st.rerun()

# Estoque
st.header("🚨 Estoque")
busca = st.text_input("🔍 Pesquisar produtos...", placeholder="Digite o nome...")
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
        st.write("### Produtos Recentes")
        cursor.execute("SELECT nome FROM historico_produtos")
        for r in cursor.fetchall(): st.code(r[0])
