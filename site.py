import streamlit as st
from datetime import datetime, date
import sqlite3

# Configuração da página
st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")

# Conexão com Banco de Dados
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL, peso REAL, unidade TEXT)")
conn.commit()

def para_float(valor):
    try: return float(valor)
    except: return 0.0

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
        if st.button("🚀 Salvar"):
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", 
                           (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f))
            conn.commit()
            st.rerun()

with col2:
    st.header("🔍 Pesquisa e Estoque")
    busca = st.text_input("🔍 Digite para pesquisar...", placeholder="Ex: Pepperoni...")
    
    produtos = carregar_produtos()
    
    # Filtra os produtos com base no texto da busca
    resultados = [p for p in produtos if busca.lower() in p['nome'].lower()]
    
    if busca:
        st.subheader(f"Resultados encontrados ({len(resultados)})")
        for item in resultados:
            dias = (item["validade"] - date.today()).days
            cor = "#000000" if dias < 0 else ("#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a"))
            
            # Formato do card: Nome | Qtd | Local
            st.markdown(f'''<div style="padding: 10px; background-color: {cor}; color: #ffffff; border-radius: 8px; margin-bottom: 8px;">
                <b>{item["nome"]}</b> - {item["quantidade"]}{item["unidade"]} <i>({item["local"]})</i> | 📅 {item["validade"].strftime("%d/%m/%Y")}
                </div>''', unsafe_html=True)
            
            c1, c2 = st.columns([1, 1])
            if c1.button("✏️ Editar", key=f"e_{item['id']}"): st.session_state.edit_data = item; st.rerun()
            if c2.button("❌ Excluir", key=f"d_{item['id']}"): cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],)); conn.commit(); st.rerun()
    else:
        # Quando não há busca, mostra todos os itens agrupados de forma simples
        st.info("Digite algo na busca para encontrar itens ou veja o estoque geral abaixo.")
        for item in produtos:
            dias = (item["validade"] - date.today()).days
            cor = "#000000" if dias < 0 else ("#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a"))
            st.markdown(f'''<div style="padding: 10px; background-color: {cor}; color: #ffffff; border-radius: 8px; margin-bottom: 8px;">
                <b>{item["nome"]}</b> - {item["quantidade"]}{item["unidade"]} <i>({item["local"]})</i>
                </div>''', unsafe_html=True)
