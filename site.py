import streamlit as st
from datetime import datetime, date
import sqlite3

# Configuração da página
st.set_page_config(page_title="Controle de Validade - Cozinha", page_icon="🍳", layout="wide")

st.title("🍳 Sistema de Controle da Cozinha")
st.write("Sistema permanente ativo. Aguardando comandos do cozinheiro **Victor**.")

conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()

# Garantir estrutura das tabelas
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, local TEXT, validade TEXT, marca TEXT, quantidade REAL, peso REAL, unidade TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY AUTOINCREMENT, item_nome TEXT, item_marca TEXT UNIQUE)")
conn.commit()

# Funções auxiliares
def carregar_produtos():
    cursor.execute("SELECT id, nome, marca, local, validade, quantidade, peso, unidade FROM produtos")
    return [{"id": l[0], "nome": l[1], "marca": l[2], "local": l[3], "validade": datetime.strptime(l[4], "%Y-%m-%d").date(), "quantidade": l[5], "peso": l[6], "unidade": l[7]} for l in cursor.fetchall()]

def carregar_historico_marcas():
    cursor.execute("SELECT DISTINCT item_marca FROM historico WHERE item_marca IS NOT NULL")
    return [l[0] for l in cursor.fetchall()]

# Lógica principal de edição
if "id_edicao" not in st.session_state: st.session_state.id_edicao = None

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Cadastrar/Editar")
    # Formulário simplificado que garante a exibição do nome
    nome_input = st.text_input("Nome do Produto")
    marca_input = st.text_input("Marca")
    local_input = st.selectbox("Local", ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"])
    qtd_input = st.number_input("Quantidade", value=1.0)
    unid_input = st.selectbox("Unidade", ["Kg", "g", "L", "mL"])
    peso_input = st.number_input("Peso/Volume", value=0.0)
    data_input = st.date_input("Validade")

    if st.button("Salvar Produto"):
        cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", 
                       (nome_input, marca_input, local_input, data_input.strftime("%Y-%m-%d"), qtd_input, peso_input, unid_input))
        if marca_input: cursor.execute("INSERT OR IGNORE INTO historico (item_marca) VALUES (?)", (marca_input,))
        conn.commit()
        st.rerun()

with col2:
    st.header("Estoque e Alarmes")
    produtos = carregar_produtos()
    for item in produtos:
        # Cálculo dinâmico que atualiza conforme o dia passa
        dias_restantes = (item["validade"] - date.today()).days
        status = "Vencido" if dias_restantes < 0 else f"{dias_restantes} dias restantes"
        
        st.write(f"**{item['nome']}** | Marca: {item['marca']} | {status}")
