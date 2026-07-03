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

# Função auxiliar de segurança para números
def para_float(valor):
    try:
        return float(valor)
    except (ValueError, TypeError):
        return 0.0

def get_historico(tipo):
    cursor.execute(f"SELECT item_{tipo} FROM historico WHERE item_{tipo} IS NOT NULL AND item_{tipo} != ''")
    return [l[0] for l in cursor.fetchall()]

def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4], "quantidade": l[5], "peso": l[6], "unidade": l[7]} for l in cursor.fetchall()]

# Estado para Edição
if "edit_data" not in st.session_state: st.session_state.edit_data = None

col1, col2 = st.columns([1, 2])

# COLUNA 1: FORMULÁRIO
with col1:
    is_editing = st.session_state.edit_data is not None
    st.header("✏️ Editar Produto" if is_editing else "📥 Cadastrar Produto")
    d = st.session_state.edit_data if is_editing else {}

    st.subheader("Nome do Produto")
    sel_nome = st.selectbox("Histórico (Nome)", [""] + get_historico("nome"), key="sel_n")
    nome_input = st.text_input("Ou novo nome:", value=d.get("nome", ""))
    nome_final = nome_input if nome_input else sel_nome

    st.subheader("Marca")
    sel_marca = st.selectbox("Histórico (Marca)", [""] + get_historico("marca"), key="sel_m")
    marca_input = st.text_input("Ou nova marca:", value=d.get("marca", ""))
    marca_final = marca_input if marca_input else sel_marca

    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais, index=locais.index(d["local"]) if is_editing and d.get("local") in locais else 0)
    
    qtd_f = st.number_input("Quantidade", value=para_float(d.get("quantidade", 1.0)))
    unidades = ["Kg", "g", "L", "mL"]
    unid_idx = unidades.index(d.get("unidade", "Kg")) if is_editing and d.get("unidade") in unidades else 0
    unid_f = st.selectbox("Unidade", unidades, index=unid_idx)
    
    peso_f = st.number_input("Peso/Volume", value=para_float(d.get("peso", 0.0)))
    data_f = st.date_input("Validade", value=d.get("validade", date.today()))

    if is_editing:
        c_sub, c_can = st.columns(2)
        if c_sub.button("💾 Atualizar"):
            cursor.execute("UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=?, peso=?, unidade=? WHERE id=?", 
                           (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f, d["id"]))
            conn.commit()
            st.session_state.edit_data = None
            st.rerun()
        if c_can.button("❌ Cancelar"):
            st.session_state.edit_data = None
            st.rerun()
    else:
        if st.button("🚀 Salvar Produto"):
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", 
                           (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f))
            if nome_final: cursor.execute("INSERT OR IGNORE INTO historico (item_nome) VALUES (?)", (nome_final,))
            if marca_final: cursor.execute("INSERT OR IGNORE INTO historico (item_marca) VALUES (?)", (marca_final,))
            conn.commit()
            st.rerun()

# COLUNA 2: ESTOQUE
with col2:
    st.header("🚨 Estoque Atual")
    produtos = carregar_produtos()
    abas = st.tabs(locais)
    
    for i, local in enumerate(locais):
        with abas[i]:
            for item in [p for p in produtos if p['local'] == local]:
                dias = (item["validade"] - date.today()).days
                
                # Cores e Status
                if dias < 0: color = "#000000" # Vencido
                elif dias <= 3: color = "#ef4444" # Crítico
                elif dias <= 7: color = "#d97706" # Atenção
                else: color = "#16a34a" # Seguro
                
                st.markdown(f'''<div style="padding: 15px; background-color: {color}; color: #ffffff; border-radius: 8px; margin-bottom: 10px;">
                    <b>{item["nome"]}</b> - {item["marca"]}<br>
                    📦 {item["quantidade"]:.0f} x {item["peso"]}{item["unidade"]} | 📅 Validade: {item["validade"].strftime("%d/%m/%Y")} ({dias} dias)
                    </div>''', unsafe_allow_html=True)
                
                col_e, col_x = st.columns(2)
                if col_e.button("✏️ Editar", key=f"edit_{item['id']}"):
                    st.session_state.edit_data = item
                    st.rerun()
                if col_x.button("❌ Excluir", key=f"del_{item['id']}"):
                    cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
                    conn.commit()
                    st.rerun()
