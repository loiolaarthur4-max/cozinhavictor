import streamlit as st
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")
st.write("Sistema permanente ativo. Aguardando comandos do cozinheiro **Victor**.")

conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()

# Tabelas
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL, peso REAL, unidade TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY AUTOINCREMENT, item_nome TEXT UNIQUE, item_marca TEXT UNIQUE)")
conn.commit()

# Funções
def get_historico(tipo):
    cursor.execute(f"SELECT item_{tipo} FROM historico WHERE item_{tipo} IS NOT NULL AND item_{tipo} != ''")
    return [l[0] for l in cursor.fetchall()]

def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4], "quantidade": l[5], "peso": l[6], "unidade": l[7]} for l in cursor.fetchall()]

# Estado de edição
if "edit_data" not in st.session_state: st.session_state.edit_data = None

col1, col2 = st.columns([1.2, 1.8])

with col1:
    is_editing = st.session_state.edit_data is not None
    st.header("✏️ Editar Produto" if is_editing else "📥 Cadastrar Produto")
    d = st.session_state.edit_data if is_editing else {}
    
    # Tratamento seguro para campos de edição
    nome_padrao = d.get("nome", "")
    marca_padrao = d.get("marca", "")
    
    st.subheader("Nome do Produto")
    opcoes_nome = [""] + get_historico("nome")
    sel_nome = st.selectbox("Histórico (Nome)", opcoes_nome, key="sel_n")
    nome_f = st.text_input("Ou novo nome:", value=nome_padrao)
    nome_final = nome_f if nome_f else sel_nome
    
    st.subheader("Marca")
    opcoes_marca = [""] + get_historico("marca")
    sel_marca = st.selectbox("Histórico (Marca)", opcoes_marca, key="sel_m")
    marca_f = st.text_input("Ou nova marca:", value=marca_padrao)
    marca_final = marca_f if marca_f else sel_marca
    
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais, index=locais.index(d["local"]) if is_editing and d["local"] in locais else 0)
    
    # Tratamento seguro de floats para não dar erro de conversão
    qtd_f = st.number_input("Quantidade", value=float(d.get("quantidade") or 1.0))
    
    op_unid = ["Kg", "g", "L", "mL"]
    unid_f = st.selectbox("Unidade", op_unid, index=op_unid.index(d.get("unidade", "Kg")) if is_editing and d.get("unidade") in op_unid else 0)
    
    peso_f = st.number_input("Peso/Volume", value=float(d.get("peso") or 0.0))
    data_f = st.date_input("Validade", value=d.get("validade", date.today()))

    if is_editing:
        c1, c2 = st.columns(2)
        if c1.button("💾 Atualizar"):
            cursor.execute("UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=?, peso=?, unidade=? WHERE id=?", 
                           (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f, d["id"]))
            conn.commit()
            st.session_state.edit_data = None
            st.rerun()
        if c2.button("❌ Cancelar"):
            st.session_state.edit_data = None
            st.rerun()
    else:
        if st.button("🚀 Adicionar"):
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", 
                           (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f))
            if nome_final: cursor.execute("INSERT OR IGNORE INTO historico (item_nome) VALUES (?)", (nome_final,))
            if marca_final: cursor.execute("INSERT OR IGNORE INTO historico (item_marca) VALUES (?)", (marca_final,))
            conn.commit()
            st.rerun()

with col2:
    st.header("🚨 Estoque por Local")
    produtos = carregar_produtos()
    abas = st.tabs(locais)
    for i, local in enumerate(locais):
        with abas[i]:
            for item in [p for p in produtos if p['local'] == local]:
                dias = (item["validade"] - date.today()).days
                bg = "#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a")
                st.markdown(f'''<div style="padding: 12px; background-color: {bg}; color: #ffffff; margin-bottom: 10px; border-radius: 8px;">
                    <b>{item["nome"]}</b> ({item["marca"]})<br>
                    📦 {item["quantidade"]:.0f}x {item["peso"]}{item["unidade"]} | 📅 {item["validade"].strftime("%d/%m/%Y")} ({dias} dias)
                    </div>''', unsafe_allow_html=True)
                
                c_e, c_d = st.columns(2)
                if c_e.button("✏️ Editar", key=f"e{item['id']}"):
                    st.session_state.edit_data = item
                    st.rerun()
                if c_d.button("❌ Excluir", key=f"d{item['id']}"):
                    cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
                    conn.commit()
                    st.rerun()
