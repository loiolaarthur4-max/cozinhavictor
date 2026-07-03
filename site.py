import streamlit as st
from datetime import datetime, date
import sqlite3

# Configuração da página
st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")

# Conexão com Banco de Dados
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()

# Criação das tabelas
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL, peso REAL, unidade TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY AUTOINCREMENT, item_nome TEXT UNIQUE, item_marca TEXT UNIQUE)")
conn.commit()

# Estilo CSS para o Scroll Fixo
st.markdown("""
    <style>
    .scroll-container {
        height: 550px;
        overflow-y: auto;
        padding-right: 10px;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

def para_float(valor):
    try: return float(valor)
    except (ValueError, TypeError): return 0.0

def get_historico(tipo):
    cursor.execute(f"SELECT item_{tipo} FROM historico WHERE item_{tipo} IS NOT NULL AND item_{tipo} != ''")
    return [l[0] for l in cursor.fetchall()]

def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4], "quantidade": l[5], "peso": l[6], "unidade": l[7]} for l in cursor.fetchall()]

if "edit_data" not in st.session_state: st.session_state.edit_data = None

col1, col2 = st.columns([1, 2])

with col1:
    is_editing = st.session_state.edit_data is not None
    st.header("✏️ Editar" if is_editing else "📥 Cadastrar")
    d = st.session_state.edit_data if is_editing else {}

    nome_final = st.text_input("Nome do Produto", value=d.get("nome", ""))
    marca_final = st.text_input("Marca", value=d.get("marca", ""))
    
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais, index=locais.index(d["local"]) if is_editing and d.get("local") in locais else 0)
    
    qtd_f = st.number_input("Quantidade", value=para_float(d.get("quantidade", 1.0)))
    unidades = ["Kg", "g", "L", "mL"]
    unid_f = st.selectbox("Unidade", unidades, index=unidades.index(d.get("unidade", "Kg")) if is_editing and d.get("unidade") in unidades else 0)
    
    peso_f = st.number_input("Peso/Volume", value=para_float(d.get("peso", 0.0)))
    data_f = st.date_input("Validade", value=d.get("validade", date.today()))

    if is_editing:
        if st.button("💾 Atualizar"):
            cursor.execute("UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=?, peso=?, unidade=? WHERE id=?", 
                           (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f, d["id"]))
            conn.commit()
            st.session_state.edit_data = None
            st.rerun()
    else:
        if st.button("🚀 Salvar"):
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", 
                           (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f))
            conn.commit()
            st.rerun()

with col2:
    st.header("🚨 Estoque Atual")
    busca = st.text_input("🔍 Pesquisar produto...", placeholder="Comece a digitar o nome...")
    produtos = carregar_produtos()
    abas = st.tabs(locais)
    
    for i, local in enumerate(locais):
        with abas[i]:
            itens = [p for p in produtos if p['local'] == local and (busca.lower() in p['nome'].lower())]
            st.write(f"📦 Total encontrado: **{len(itens)}**")
            
            st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
            for item in itens:
                dias = (item["validade"] - date.today()).days
                color = "#000000" if dias < 0 else ("#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a"))
                
                st.markdown(f'''<div style="padding: 10px; background-color: {color}; color: #ffffff; border-radius: 8px; margin-bottom: 8px;">
                    <b>{item["nome"]}</b> ({item["marca"]}) - 📅 {item["validade"].strftime("%d/%m/%Y")} ({dias} dias)
                    </div>''', unsafe_allow_html=True)
                
                c1, c2 = st.columns([1, 1])
                if c1.button("✏️", key=f"e_{item['id']}"): st.session_state.edit_data = item; st.rerun()
                if c2.button("❌", key=f"d_{item['id']}"): cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],)); conn.commit(); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
