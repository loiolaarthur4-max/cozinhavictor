import streamlit as st
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Controle de Validade", page_icon="🍳", layout="wide")
st.title("🍳 Sistema de Controle da Cozinha")

# Conexão
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_produtos (nome TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_marcas (nome TEXT UNIQUE)")
conn.commit()

# Controle de estado para a câmera
if "camera_ativa" not in st.session_state:
    st.session_state.camera_ativa = False

def alternar_camera():
    st.session_state.camera_ativa = not st.session_state.camera_ativa

# Funções de busca e renderização
def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4], "quantidade": l[5]} for l in cursor.fetchall()]

# Sidebar
with st.sidebar:
    st.header("📷 Scanner")
    if st.button("🔌 Ligar/Desligar Câmera"):
        alternar_camera()
    
    if st.session_state.camera_ativa:
        st.camera_input("Foto para referência", key="scanner_foto")
    
    st.markdown("---")
    st.header("📥 Cadastrar Produto")
    nome_f = st.text_input("Nome do Produto")
    marca_f = st.text_input("Marca")
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais)
    qtd_f = st.number_input("Quantidade", value=1.0, step=1.0)
    data_f = st.date_input("Validade", value=date.today())

    if st.button("🚀 Salvar"):
        cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade) VALUES (?,?,?,?,?)", 
                       (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f))
        conn.commit()
        st.success("Salvo!")
        st.rerun()

# Conteúdo Principal
st.header("🚨 Estoque")
busca = st.text_input("🔍 Pesquisar produtos...")
produtos = carregar_produtos()

def exibir_lista(lista_produtos):
    for item in lista_produtos:
        dias = (item["validade"] - date.today()).days
        cor = "#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f'''<div style="padding: 10px; background-color: {cor}; color: white; border-radius: 8px;">
                <b>{item["nome"]}</b> | <b>Marca:</b> {item["marca"]} | 📅 {dias} dias</div>''', unsafe_allow_html=True)
        with col2:
            if st.button("❌", key=f"del_{item['id']}"):
                cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
                conn.commit()
                st.rerun()

if busca:
    exibir_lista([p for p in produtos if busca.lower() in p['nome'].lower()])
else:
    abas = st.tabs(locais + ["📜 Histórico"])
    for i, local in enumerate(locais):
        with abas[i]:
            exibir_lista([p for p in produtos if p['local'] == local])
    
    with abas[-1]:
        st.write("### Histórico de Cadastros")
        cursor.execute("SELECT nome FROM historico_produtos")
        for r in cursor.fetchall(): st.write(f"- {r[0]}")
