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

# Funções de busca
def get_historico(tipo):
    cursor.execute(f"SELECT item_{tipo} FROM historico WHERE item_{tipo} IS NOT NULL AND item_{tipo} != ''")
    return [l[0] for l in cursor.fetchall()]

def carregar_produtos():
    cursor.execute("SELECT * FROM produtos")
    return [{"id": l[0], "nome": l[1], "local": l[2], "validade": datetime.strptime(l[3], "%Y-%m-%d").date(), "marca": l[4], "quantidade": l[5], "peso": l[6], "unidade": l[7]} for l in cursor.fetchall()]

# Lógica de Edição (Armazena temporariamente para editar)
if "id_edicao" not in st.session_state: st.session_state.id_edicao = None

col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.header("📥 Cadastrar/Editar Produto")
    
    st.subheader("Nome do Produto")
    opcoes_nome = [""] + get_historico("nome")
    sel_nome = st.selectbox("Selecionar do Histórico", opcoes_nome)
    novo_nome = st.text_input("Ou digitar NOVO nome:")
    nome_final = novo_nome if novo_nome else sel_nome
    
    st.subheader("Marca")
    opcoes_marca = [""] + get_historico("marca")
    sel_marca = st.selectbox("Selecionar do Histórico", opcoes_marca)
    nova_marca = st.text_input("Ou digitar NOVA marca:")
    marca_final = nova_marca if nova_marca else sel_marca
    
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais)
    qtd_f = st.number_input("Quantidade", value=1.0)
    unid_f = st.selectbox("Unidade", ["Kg", "g", "L", "mL"])
    peso_f = st.number_input("Peso/Volume", value=0.0)
    data_f = st.date_input("Validade")

    if st.button("🚀 Salvar Produto"):
        if nome_final:
            if st.session_state.id_edicao:
                cursor.execute("UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=?, peso=?, unidade=? WHERE id=?", 
                               (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f, st.session_state.id_edicao))
                st.session_state.id_edicao = None
            else:
                cursor.execute("INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?,?,?,?,?,?,?)", 
                               (nome_final, marca_final, local_f, data_f.strftime("%Y-%m-%d"), qtd_f, peso_f, unid_f))
            
            if novo_nome: cursor.execute("INSERT OR IGNORE INTO historico (item_nome) VALUES (?)", (novo_nome,))
            if nova_marca: cursor.execute("INSERT OR IGNORE INTO historico (item_marca) VALUES (?)", (nova_marca,))
            conn.commit()
            st.rerun()

with col2:
    st.header("🚨 Estoque por Local")
    produtos = carregar_produtos()
    abas = st.tabs(locais)
    
    for i, local in enumerate(locais):
        with abas[i]:
            filtrados = [p for p in produtos if p['local'] == local]
            for item in filtrados:
                dias = (item["validade"] - date.today()).days
                # Lógica de cores opostas (fundo escuro/claro com texto contrastante)
                bg_color = "#ef4444" if dias <= 3 else ("#d97706" if dias <= 7 else "#16a34a")
                text_color = "#ffffff" # Texto branco para contrastar com as cores vibrantes dos estados
                
                st.markdown(f"""
                <div style="padding: 12px; background-color: {bg_color}; color: {text_color}; margin-bottom: 10px; border-radius: 8px;">
                    <b style="font-size: 1.2em;">{item['nome']}</b> {f'({item['marca']})' if item['marca'] else ''}<br>
                    📦 {item['quantidade']:.0f} un x {item['peso']}{item['unidade']} | 📅 Validade: {item['validade'].strftime('%d/%m/%Y')} <b>({dias} dias)</b>
                </div>
                """, unsafe_allow_html=True)
                
                c_edit, c_del = st.columns(2)
                if c_edit.button("✏️ Editar", key=f"edit_{item['id']}"):
                    st.session_state.id_edicao = item['id']
                    # Você pode implementar aqui o carregamento dos dados atuais no formulário se desejar
                    st.rerun()
                if c_del.button("❌ Excluir", key=f"del_{item['id']}"):
                    cursor.execute("DELETE FROM produtos WHERE id=?", (item['id'],))
                    conn.commit()
                    st.rerun()
