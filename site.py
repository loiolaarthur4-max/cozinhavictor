import streamlit as st
from datetime import datetime, date
import sqlite3
import time

# Configuração da página do site
st.set_page_config(page_title="Controle de Validade - Cozinha", page_icon="🍳", layout="wide")

# Título principal do Site
st.title("🍳 Sistema de Controle da Cozinha")
st.write("Sistema permanente ativo. Aguardando comandos do cozinheiro **Victor**.")

# --- CONEXÃO COM BANCO DE DADOS (SQLITE) ---
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()

# 1. Cria a tabela básica se ela não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    local TEXT,
    validade TEXT
)
""")
conn.commit()

# 2. Upgrade automático para adicionar a coluna 'marca' caso não exista
try:
    cursor.execute("ALTER TABLE produtos ADD COLUMN marca TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

# 3. Cria a tabela de histórico de sugestões
cursor.execute("""
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_nome TEXT UNIQUE,
    item_marca TEXT
)
""")
conn.commit()

# FUNÇÃO PARA CARREGAR PRODUTOS DO ESTOQUE (Agora puxando o ID também)
def carregar_produtos():
    cursor.execute("SELECT id, nome, marca, local, validade FROM produtos")
    linhas = cursor.fetchall()
    lista_produtos = []
    for linha in linhas:
        marca_produto = linha[2] if linha[2] else ""
        lista_produtos.append({
            "id": linha[0], # Guardamos o ID numérico para saber quem deletar
            "nome": linha[1],
            "marca": marca_produto,
            "local": linha[3],
            "validade": datetime.strptime(linha[4], "%Y-%m-%d").date()
        })
    return lista_produtos

def carregar_historico_nomes():
    cursor.execute("SELECT item_nome FROM historico ORDER BY item_nome ASC")
    return [linha[0] for linha in cursor.fetchall()]

def carregar_historico_marcas():
    cursor.execute("SELECT DISTINCT item_marca FROM historico WHERE item_marca IS NOT NULL AND item_marca != '' ORDER BY item_marca ASC")
    return [linha[0] for linha in cursor.fetchall()]

if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_produtos()

if "backup_produtos" not in st.session_state:
    st.session_state.backup_produtos = None
if "tempo_limpeza" not in st.session_state:
    st.session_state.tempo_limpeza = 0

# Divisão em duas colunas
col1, col2 = st.columns([1, 2])

# COLUNA 1: Formulário de Cadastro
with col1:
    st.header("📥 Cadastrar Novo Produto")
    
    lista_sugestoes_nome = carregar_historico_nomes()
    lista_sugestoes_marca = carregar_historico_marcas()
    
    nome = st.selectbox("Nome do Alimento / Bebida (Selecione do histórico):", options=[""] + lista_sugestoes_nome, index=0)
    nome_novo = st.text_input("Ou digite um NOVO nome:")
    nome_final = nome_novo.strip() if nome_novo else nome
    
    marca = st.selectbox("Marca do Produto (Selecione do histórico):", options=[""] + lista_sugestoes_marca, index=0)
    marca_nova = st.text_input("Ou digite uma NOVA marca:")
    marca_final = marca_nova.strip() if marca_nova else marca

    local = st.selectbox("Onde este produto será guardado?", [
        "Geladeira Principal (1)", 
        "Freezer Branco", 
        "Freezer Red Bull", 
        "Freezer Grande"
    ])
    
    data_val = st.date_input("Data de Validade do Produto:", min_value=date.today())
    
    if st.button("Adicionar ao Estoque"):
        if nome_final:
            data_texto = data_val.strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO produtos (nome, marca, local, validade) VALUES (?, ?, ?, ?)", (nome_final, marca_final, local, data_texto))
            cursor.execute("INSERT OR IGNORE INTO historico (item_nome, item_marca) VALUES (?, ?)", (nome_final, marca_final))
            conn.commit()
            
            st.session_state.produtos = carregar_produtos()
            st.session_state.backup_produtos = None 
            st.success("🟢 {0} adicionado com sucesso!".format(nome_final))
            st.rerun()
        else:
            st.error("⚠️ Por favor, selecione ou digite o nome do produto.")

# COLUNA 2: O painel de Alarmes com Exclusão Individual
with col2:
    st.header("🚨 Alarmes e Estoque Atual")
    
    # LÓGICA DO BOTÃO DESFAZER (Para quando apagar TUDO)
    if st.session_state.backup_produtos is not None:
        tempo_passado = time.time() - st.session_state.tempo_limpeza
        tempo_restante = int(10 - tempo_passado)
        
        if tempo_restante > 0:
            st.warning("⚠️ Todo o estoque foi apagado!")
            if st.button("🔄 DESFAZER AÇÃO ({0}s)".format(tempo_restante)):
                for item in st.session_state.backup_produtos:
                    cursor.execute("INSERT INTO produtos (nome, marca, local, validade) VALUES (?, ?, ?, ?)", (item["nome"], item["marca"], item["local"], item["validade"].strftime("%Y-%m-%d")))
                conn.commit()
                st.session_state.produtos = carregar_produtos()
                st.session_state.backup_produtos = None
                st.success("✅ Estoque recuperado com sucesso!")
                st.rerun()
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.backup_produtos = None
            st.rerun()

    if len(st.session_state.produtos) == 0 and st.session_state.backup_produtos is None:
        st.info("O estoque está completamente vazio. Victor pode começar a enviar os produtos!")
    
    elif len(st.session_state.produtos) > 0:
        if st.button("🗑️ Limpar Todo o Estoque"):
            st.session_state.backup_produtos = st.session_state.produtos.copy()
            st.session_state.tempo_limpeza = time.time()
            cursor.execute("DELETE FROM produtos")
            conn.commit()
            st.session_state.produtos = []
            st.rerun()
            
        st.write("---")
        
        # Lista os produtos criandos colunas menores para o botão de apagar
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
            
            texto_marca = " ({0})".format(item['marca']) if item['marca'] else ""
            
            # Divide a linha do card em duas: 85% para o card e 15% para o botão de deletar
            card_col, btn_col = st.columns([6, 1])
            
            with card_col:
                html_card = (
                    '<div style="padding: 12px; border-radius: 8px; border-left: 6px solid ' + cor_alarme + '; '
                    'background-color: ' + cor_fundo + '; margin-bottom: 12px; color: #1e293b; font-family: sans-serif;">'
                    '<span style="font-size: 12pt; font-weight: bold;">' + str(item['nome']) + texto_marca + '</span> <br>'
                    '<span style="font-size: 10pt;">📍 Local: <b>' + str(item['local']) + '</b> | Validade: ' + item['validade'].strftime('%d/%m/%Y') + '</span><br>'
                    '<span style="font-size: 10.5pt; font-weight: bold; color: ' + cor_alarme + ';">' + status_texto + '</span>'
                    '</div>'
                )
                st.html(html_card)
                
            with btn_col:
                # Cria um espaço vertical para alinhar o botão ao meio do card
                st.write("")
                # Botão de deletar individual usando o ID único do item no banco
                if st.button("❌", key="del_{0}".format(item['id']), help="Remover apenas este produto"):
                    cursor.execute("DELETE FROM produtos WHERE id = ?", (item['id'],))
                    conn.commit()
                    st.session_state.produtos = carregar_produtos()
                    st.success("Removido!")
                    st.rerun()
