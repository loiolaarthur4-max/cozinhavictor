import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, date
import sqlite3

# Configuração da Página
st.set_page_config(page_title="Controle Cozinha", layout="wide")

# Conexão com banco
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_produtos (nome TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico_marcas (nome TEXT UNIQUE)")
conn.commit()

# Script do Scanner (HTML/JS)
def scanner_js():
    return """
    <div id="reader" style="width: 100%;"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        function onScanSuccess(decodedText) {
            var input = window.parent.document.querySelector('input[type="text"]');
            input.value = decodedText;
            input.dispatchEvent(new Event('input', {bubbles: true}));
        }
        let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess);
    </script>
    """

# Título
st.title("🍳 Sistema de Controle da Cozinha")

# Sidebar
with st.sidebar:
    st.header("📷 Scanner Automático")
    if st.button("Abrir Câmera"):
        components.html(scanner_js(), height=450)
    
    st.header("📥 Cadastrar Produto")
    nome_f = st.text_input("Nome do Produto (ou escaneie)")
    marca_f = st.text_input("Marca")
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais)
    qtd_f = st.number_input("Quantidade", value=1.0)
    data_f = st.date_input("Validade")

    if st.button("🚀 Salvar"):
        cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade) VALUES (?,?,?,?,?)", 
                       (nome_f, marca_f, local_f, data_f.strftime("%Y-%m-%d"), qtd_f))
        cursor.execute("INSERT OR IGNORE INTO historico_produtos (nome) VALUES (?)", (nome_f,))
        conn.commit()
        st.rerun()

# Conteúdo Principal
st.header("🚨 Estoque")
busca = st.text_input("🔍 Pesquisar...")
produtos = [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4]} for l in cursor.execute("SELECT * FROM produtos").fetchall()]

def render_lista(lista):
    for item in lista:
        dias = (item["validade"] - date.today()).days
        cor = "#ef4444" if dias <= 3 else "#16a34a"
        c1, c2 = st.columns([5, 1])
        c1.markdown(f'<div style="background:{cor}; color:white; padding:10px; border-radius:5px;">{item["nome"]} - {item["marca"]} ({dias} dias)</div>', unsafe_allow_html=True)
        if c2.button("❌", key=f"del_{item['id']}"):
            cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
            conn.commit()
            st.rerun()

if busca:
    render_lista([p for p in produtos if busca.lower() in p['nome'].lower()])
else:
    abas = st.tabs(locais + ["📜 Histórico"])
    for i, loc in enumerate(locais):
        with abas[i]:
            render_lista([p for p in produtos if p['local'] == loc])
    with abas[-1]:
        st.subheader("Histórico de Produtos")
        for r in cursor.execute("SELECT nome FROM historico_produtos").fetchall(): 
            st.write(f"- {r[0]}")
