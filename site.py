import streamlit as st
from datetime import datetime, date
import sqlite3

# Configuração da página do site
st.set_page_config(page_title="Controle de Validade - Cozinha", page_icon="🍳", layout="wide")

# Título principal do Site
st.title("🍳 Sistema de Controle da Cozinha")
st.write("Sistema permanente ativo. Aguardando comandos do cozinheiro **Victor**.")

# --- CONEXÃO COM BANCO DE DADOS DE VERDADE (SQLITE) ---
# Cria um arquivo de banco de dados real que não apaga ao fechar o site
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()

# Cria a tabela de produtos se ela não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    local TEXT,
    validade TEXT
)
""")
conn.commit()

# FUNÇÃO PARA CARREGAR OS PRODUTOS DO BANCO
def carregar_produtos():
    cursor.execute("SELECT nome, local, validade FROM produtos")
    linhas = cursor.fetchall()
    lista_produtos = []
    for linha in linhas:
        lista_produtos.append({
            "nome": linha[0],
            "local": linha[1],
            "validade": datetime.strptime(linha[2], "%Y-%m-%d").date()
        })
    return lista_produtos

# Carrega os produtos direto do banco de dados permanente
if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_produtos()

# Divisão da tela em duas colunas
col1, col2 = st.columns([1, 2])

# COLUNA 1: Formulário para o Victor digitar os produtos
with col1:
    st.header("📥 Cadastrar Novo Produto")
    
    nome = st.text_input("Nome do Alimento / Bebida:", placeholder="Ex: Queijo, Leite, Carne...")
    
    local = st.selectbox("Onde este produto será guardado?", [
        "Geladeira Principal (1)", 
        "Freezer Branco", 
        "Freezer Red Bull", 
        "Freezer Grande"
    ])
    
    data_val = st.date_input("Data de Validade do Produto:", min_value=date.today())
    
    if st.button("Adicionar ao Estoque"):
        if nome:
            nome_limpo = nome.strip()
            data_texto = data_val.strftime("%Y-%m-%d")
            
            # Insere permanentemente no banco de dados
            cursor.execute("INSERT INTO produtos (nome, local, validade) VALUES (?, ?, ?)", (nome_limpo, local, data_texto))
            conn.commit()
            
            # Atualiza a tela
            st.session_state.produtos = carregar_produtos()
            st.success("🟢 {0} adicionado e salvo permanentemente!".format(nome_limpo))
            st.rerun()
        else:
            st.error("⚠️ Por favor, digite o nome do produto antes de adicionar.")

# COLUNA 2: O painel de Alarmes Automáticos (Interface Idêntica)
with col2:
    st.header("🚨 Alarmes e Estoque Atual")
    
    if len(st.session_state.produtos) == 0:
        st.info("O estoque está completamente vazio. Victor pode começar a enviar os produtos!")
    else:
        if st.button("🗑️ Limpar Todo o Estoque"):
            cursor.execute("DELETE FROM produtos")
            conn.commit()
            st.session_state.produtos = []
            st.rerun()
            
        st.write("---")
        
        for item in st.session_state.produtos:
            hoje = date.today()
            dias_restantes = (item["validade"] - hoje).days
            
            if dias_restantes < 0:
                status_texto = "❌ VENCIDO HÁ {0} DIAS!".format(abs(dias_restantes))
                cor_alarme = "#ef4444"
                cor_fundo = "#fee2e2"
            elif dias_restantes <= 3:
                status_texto = "🚨 CRÍTICO! Vence em {0} dias.".format(dias_restantes)
                cor_alarme = "#dc2626"
                cor_fundo = "#fee2e2"
            elif dias_restantes <= 7:
                status_texto = "⚠️ ATENÇÃO! Vence em {0} dias.".format(dias_restantes)
                cor_alarme = "#d97706"
                cor_fundo = "#fef3c7"
            else:
                status_texto = "✅ Seguro ({0} dias restantes)".format(dias_restantes)
                cor_alarme = "#16a34a"
                cor_fundo = "#dcfce7"
            
            html_card = (
                '<div style="padding: 12px; border-radius: 8px; border-left: 6px solid ' + cor_alarme + '; '
                'background-color: ' + cor_fundo + '; margin-bottom: 12px; color: #1e293b; font-family: sans-serif;">'
                '<span style="font-size: 12pt; font-weight: bold;">' + str(item['nome']) + '</span> <br>'
                '<span style="font-size: 10pt;">📍 Local: <b>' + str(item['local']) + '</b> | Validade: ' + item['validade'].strftime('%d/%m/%Y') + '</span><br>'
                '<span style="font-size: 10.5pt; font-weight: bold; color: ' + cor_alarme + ';">' + status_texto + '</span>'
                '</div>'
            )
            st.html(html_card)
