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

# Cria a tabela de produtos
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    marca TEXT,
    local TEXT,
    validade TEXT
)
""")

# Cria a tabela separada para armazenar o histórico de sugestões
cursor.execute("""
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_nome TEXT UNIQUE,
    item_marca TEXT
)
""")
conn.commit()

# FUNÇÃO PARA CARREGAR PRODUTOS DO ESTOQUE
def carregar_produtos():
    cursor.execute("SELECT nome, marca, local, validade FROM produtos")
    linhas = cursor.fetchall()
    lista_produtos = []
    for linha in linhas:
        # Garante que se a marca for antiga/nula, não quebre o código
        marca_produto = linha[1] if linha[1] else ""
        lista_produtos.append({
            "nome": linha[0],
            "marca": marca_produto,
            "local": Henry_local := linha[2],
            "validade": datetime.strptime(linha[3], "%Y-%m-%d").date()
        })
    return lista_produtos

# FUNÇÃO PARA PEGAR OS NOMES JÁ CADASTRADOS NO HISTÓRICO
def carregar_historico_nomes():
    cursor.execute("SELECT item_nome FROM historico ORDER BY item_nome ASC")
    return [linha[0] for linha in cursor.fetchall()]

# FUNÇÃO PARA PEGAR AS MARCAS JÁ CADASTRADAS NO HISTÓRICO
def carregar_historico_marcas():
    cursor.execute("SELECT DISTINCT item_marca FROM historico WHERE item_marca IS NOT NOT NULL AND item_marca != '' ORDER BY item_marca ASC")
    return [linha[0] for linha in cursor.fetchall()]

if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_produtos()

# Inicializa as variáveis da memória para o sistema de "Desfazer"
if "backup_produtos" not in st.session_state:
    st.session_state.backup_produtos = None
if "tempo_limpeza" not in st.session_state:
    st.session_state.tempo_limpeza = 0

# Divisão em duas colunas
col1, col2 = st.columns([1, 2])

# COLUNA 1: Formulário de Cadastro com Histórico Autocomplete
with col1:
    st.header("📥 Cadastrar Novo Produto")
    
    # Busca o histórico atualizado do banco de dados
    lista_sugestoes_nome = carregar_historico_nomes()
    lista_sugestoes_marca = carregar_historico_marcas()
    
    # Caixinha de entrada com histórico integrado (st.selectbox com opção de digitar)
    nome = st.selectbox(
        "Nome do Alimento / Bebida (Digite ou selecione do histórico):",
        options=[""] + lista_sugestoes_nome,
        index=0,
        placeholder="Ex: Presunto, Leite, Queijo..."
    )
    
    # Se ele preferir digitar um nome totalmente novo que não está no histórico:
    nome_novo = st.text_input("Ou digite um NOVO nome caso não esteja no histórico acima:")
    nome_final = nome_novo.strip() if nome_novo else nome
    
    # Aba/Caixinha de Marca também com histórico em scroll
    marca = st.selectbox(
        "Marca do Produto (Digite ou selecione do histórico):",
        options=[""] + lista_sugestoes_marca,
        index=0,
        placeholder="Ex: Seara, Nestlé, Itambé..."
    )
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
            
            # 1. Salva permanentemente na tabela de estoque atual
            cursor.execute(
                "INSERT INTO produtos (nome, marca, local, validade) VALUES (?, ?, ?, ?)", 
                (nome_final, marca_final, local, data_texto)
            )
            
            # 2. Salva inteligentemente no Histórico para aparecer nas próximas vezes
            cursor.execute(
                "INSERT OR IGNORE INTO historico (item_nome, item_marca) VALUES (?, ?)", 
                (nome_final, marca_final)
            )
            conn.commit()
            
            st.session_state.produtos = carregar_produtos()
            st.session_state.backup_produtos = None 
            st.success("🟢 {0} adicionado e salvo no histórico!".format(nome_final))
            st.rerun()
        else:
            st.error("⚠️ Por favor, selecione ou digite o nome do produto.")

# COLUNA 2: Painel de Alarmes e Visualização
with col2:
    st.header("🚨 Alarmes e Estoque Atual")
    
    # LÓGICA DO BOTÃO DESFAZER
    if st.session_state.backup_produtos is not None:
        tempo_passado = time.time() - st.session_state.tempo_limpeza
        tempo_restante = int(10 - tempo_passado)
        
        if tempo_restante > 0:
            st.warning("⚠️ Todo o estoque foi apagado!")
            if st.button("🔄 DESFAZER AÇÃO ({0}s)".format(tempo_restante)):
                for item in st.session_state.backup_produtos:
                    cursor.execute(
                        "INSERT INTO produtos (nome, marca, local, validade) VALUES (?, ?, ?, ?)", 
                        (item["nome"], item["marca"], item["local"], item["validade"].strftime("%Y-%m-%d"))
                    )
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
        
        for item in st.session_state.produtos:
            hoje = date.today()
            dias_restantes = (item["validade"] - hoje).days
            
            if dias_restantes < 0:
                status_texto = "❌ VENCIDO HÁ {0} DIAS!".format(abs(dias_restantes))
                cor_alarme = "#ef4444"
                cor_fundo = "#fee2e2"
            elif dias_restantes <= 3:
                status_texto = "🚨 CRÍTICO! Vence in {0} dias.".format(dias_restantes)
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
            
            # Exibe o Nome e a Marca destacados no Card
            texto_marca = " ({0})".format(item['marca']) if item['marca'] else ""
            
            html_card = (
                '<div style="padding: 12px; border-radius: 8px; border-left: 6px solid ' + cor_alarme + '; '
                'background-color: ' + cor_fundo + '; margin-bottom: 12px; color: #1e293b; font-family: sans-serif;">'
                '<span style="font-size: 12pt; font-weight: bold;">' + str(item['nome']) + texto_marca + '</span> <br>'
                '<span style="font-size: 10pt;">📍 Local: <b>' + str(item['local']) + '</b> | Validade: ' + item['validade'].strftime('%d/%m/%Y') + '</span><br>'
                '<span style="font-size: 10.5pt; font-weight: bold; color: ' + cor_alarme + ';">' + status_texto + '</span>'
                '</div>'
            )
            st.html(html_card)
