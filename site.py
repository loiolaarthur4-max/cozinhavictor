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

# 1. Cria a tabela básica de produtos se ela não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    local TEXT,
    validade TEXT
)
""")
conn.commit()

# 2. UPGRADES AUTOMÁTICOS DE COLUNAS
colunas_para_adicionar = [
    ("marca", "TEXT"),
    ("quantidade", "REAL DEFAULT 1.0"),
    ("unidade", "TEXT DEFAULT 'Unidades'")
]

for coluna, tipo in colunas_para_adicionar:
    try:
        cursor.execute("ALTER TABLE produtos ADD COLUMN {0} {1}".format(coluna, tipo))
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

# FUNÇÃO PARA CARREGAR PRODUTOS DO ESTOQUE
def carregar_produtos():
    cursor.execute("SELECT id, nome, marca, local, validade, quantidade, unidade FROM produtos")
    linhas = cursor.fetchall()
    lista_produtos = []
    for linha in linhas:
        marca_produto = linha[2] if linha[2] else ""
        qtd_produto = linha[5] if (len(linha) > 5 and linha[5] is not None) else 1.0
        unidade_produto = linha[6] if (len(linha) > 6 and linha[6]) else "Unidades"
        
        lista_produtos.append({
            "id": linha[0],
            "nome": linha[1],
            "marca": marca_produto,
            "local": Henry_loc_item := linha[3],
            "validade": datetime.strptime(linha[4], "%Y-%m-%d").date(),
            "quantidade": qtd_produto,
            "unidade": unidade_produto
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

# Divisão em duas colunas principais
col1, col2 = st.columns([1.1, 1.7])

# COLUNA 1: Cadastro dividido em Abas Separadas
with col1:
    st.header("📥 Cadastrar Novo Produto")
    
    lista_sugestoes_nome = carregar_historico_nomes()
    lista_sugestoes_marca = carregar_historico_marcas()
    
    # CRIAÇÃO DAS ABAS
    aba_unidades, aba_peso = st.tabs(["📦 Cadastro por Unidade", "⚖️ Cadastro por Peso (Kg/g)"])
    
    # --- ABA 1: APENAS UNIDADES ---
    with aba_unidades:
        st.subheader("Itens Contáveis (Caixas, Latas, Garrafas)")
        
        nome_uni = st.selectbox("Nome do Alimento (Histórico):", options=[""] + lista_sugestoes_nome, index=0, key="sel_uni")
        nome_novo_uni = st.text_input("Ou digite um NOVO nome:", key="txt_uni")
        nome_final_uni = nome_novo_uni.strip() if nome_novo_uni else nome_uni
        
        marca_uni = st.selectbox("Marca (Histórico):", options=[""] + lista_sugestoes_marca, index=0, key="mar_uni")
        marca_nova_uni = st.text_input("Ou digite uma NOVA marca:", key="txt_mar_uni")
        marca_final_uni = marca_nova_uni.strip() if marca_nova_uni else marca_uni

        local_uni = st.selectbox("Onde guardar?", ["Geladeira Principal (1)", "Freezer Branco", "Freezer Red Bull", "Freezer Grande"], key="loc_uni")
        
        qtd_uni = st.number_input("Quantidade (Inteira):", min_value=1.0, value=1.0, step=1.0, format="%.0f", key="qtd_uni")
        data_val_uni = st.date_input("Data de Validade:", min_value=date.today(), key="dat_uni")
        
        if st.button("Adicionar Unidade(s) ao Estoque", key="btn_cad_uni"):
            if nome_final_uni:
                data_texto = data_val_uni.strftime("%Y-%m-%d")
                cursor.execute(
                    "INSERT INTO produtos (nome, marca, local, validade, quantidade, unidade) VALUES (?, ?, ?, ?, ?, ?)",
                    (nome_final_uni, marca_final_uni, local_uni, data_texto, qtd_uni, "Unidades")
                )
                cursor.execute("INSERT OR IGNORE INTO historico (item_nome, item_marca) VALUES (?, ?)", (nome_final_uni, marca_final_uni))
                conn.commit()
                st.session_state.produtos = carregar_produtos()
                st.success(f"🟢 {nome_final_uni} adicionado!")
                st.rerun()
            else:
                st.error("⚠️ Digite ou selecione o nome do produto.")

    # --- ABA 2: APENAS PESO (KG OU G) ---
    with aba_peso:
        st.subheader("Itens Pesados (Carnes, Frios, Grãos, Massas)")
        
        nome_peso = st.selectbox("Nome do Alimento (Histórico):", options=[""] + lista_sugestoes_nome, index=0, key="sel_peso")
        nome_novo_peso = st.text_input("Ou digite um NOVO nome:", key="txt_peso")
        nome_final_peso = nome_novo_peso.strip() if nome_novo_peso else nome_peso
        
        marca_peso = st.selectbox("Marca (Histórico):", options=[""] + lista_sugestoes_marca, index=0, key="mar_peso")
        marca_nova_peso = st.text_input("Ou digite uma NOVA marca:", key="txt_mar_peso")
        marca_final_peso = marca_nova_peso.strip() if marca_nova_peso else marca_peso

        local_peso = st.selectbox("Onde guardar?", ["Geladeira Principal (1)", "Freezer Branco", "Freezer Red Bull", "Freezer Grande"], key="loc_peso")
        
        # Botão de seleção para Victor escolher se quer salvar em Kg ou g
        unidade_peso_escolhida = st.radio("Escolha a unidade de medida:", ["Kg", "g"], horizontal=True, key="escolha_unidade_peso")
        
        if unidade_peso_escolhida == "Kg":
            qtd_peso = st.number_input("Peso em Quilos (Ex: 1.50):", min_value=0.01, value=1.0, step=0.1, format="%.2f", key="num_kg")
        else:
            qtd_peso = st.number_input("Peso em Gramas (Ex: 500):", min_value=1.0, value=500.0, step=50.0, format="%.0f", key="num_g")
            
        data_val_peso = st.date_input("Data de Validade:", min_value=date.today(), key="dat_peso")
        
        if st.button("Adicionar Peso ao Estoque", key="btn_cad_peso"):
            if nome_final_peso:
                data_texto = data_val_peso.strftime("%Y-%m-%d")
                # AQUI ESTÁ CORRIGIDO: Salvando a unidade_peso_escolhida ("Kg" ou "g") direto no banco!
                cursor.execute(
                    "INSERT INTO produtos (nome, marca, local, validade, quantidade, unidade) VALUES (?, ?, ?, ?, ?, ?)", 
                    (nome_final_peso, marca_final_peso, local_peso, data_texto, qtd_peso, unidade_peso_escolhida)
                )
                cursor.execute("INSERT OR IGNORE INTO historico (item_nome, item_marca) VALUES (?, ?)", (nome_final_peso, marca_final_peso))
                conn.commit()
                st.session_state.produtos = carregar_produtos()
                st.success(f"🟢 {nome_final_peso} adicionado com peso correto!")
                st.rerun()
            else:
                st.error("⚠️ Digite ou selecione o nome do produto.")

# COLUNA 2: Painel de Estoque e Controles
with col2:
    st.header("🚨 Alarmes e Estoque Atual")
    
    if st.session_state.backup_produtos is not None:
        tempo_passado = time.time() - st.session_state.tempo_limpeza
        tempo_restante = int(10 - tempo_passado)
        
        if tempo_restante > 0:
            st.warning("⚠️ Todo o estoque foi apagado!")
            if st.button("🔄 DESFAZER AÇÃO ({0}s)".format(tempo_restante)):
                for item in st.session_state.backup_produtos:
                    cursor.execute(
                        "INSERT INTO produtos (nome, marca, local, validade, quantidade, unidade) VALUES (?, ?, ?, ?, ?, ?)", 
                        (item["nome"], item["marca"], item["local"], item["validade"].strftime("%Y-%m-%d"), item["quantidade"], item["unidade"])
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
        if st.button("🗑️ Limpar Todo O Estoque"):
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
            
            unidade_card = item['unidade']
            qtd_card = item['quantidade']
            
            if unidade_card == "Kg":
                texto_qtd = "{:.2f} Kg".format(qtd_card)
            elif unidade_card == "g":
                texto_qtd = "{:.0f} g".format(qtd_card)
            else:
                texto_qtd = "{:.0f} Unid.".format(qtd_card)
            
            card_col, control_col = st.columns([3.5, 1.5])
            
            with card_col:
                html_card = (
                    '<div style="padding: 12px; border-radius: 8px; border-left: 6px solid ' + cor_alarme + '; '
                    'background-color: ' + cor_fundo + '; margin-bottom: 12px; color: #1e293b; font-family: sans-serif;">'
                    '<span style="font-size: 12pt; font-weight: bold;">' + str(item['nome']) + texto_marca + '</span> <br>'
                    '<span style="font-size: 10.5pt; color: #0f172a;">📦 Estoque: <b>' + texto_qtd + '</b></span><br>'
                    '<span style="font-size: 9.5pt;">📍 Local: <b>' + str(item['local']) + '</b> | Validade: ' + item['validade'].strftime('%d/%m/%Y') + '</span><br>'
                    '<span style="font-size: 10.5pt; font-weight: bold; color: ' + cor_alarme + ';">' + status_texto + '</span>'
                    '</div>'
                )
                st.html(html_card)
                
            with control_col:
                st.write("") 
                c1, c2, c3 = st.columns([1, 1, 1])
                
                passo = 0.1 if unidade_card == "Kg" else (50.0 if unidade_card == "g" else 1.0)
                
                with c1:
                    if st.button("➖", key="sub_{0}".format(item['id'])):
                        nova_qtd = qtd_card - passo
                        if nova_qtd <= 0:
                            cursor.execute("DELETE FROM produtos WHERE id = ?", (item['id'],))
                        else:
                            cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_qtd, item['id']))
                        conn.commit()
                        st.session_state.produtos = carregar_produtos()
                        st.rerun()
                        
                with c2:
                    if st.button("➕", key="add_{0}".format(item['id'])):
                        nova_qtd = qtd_card + passo
                        cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_qtd, item['id']))
                        conn.commit()
                        st.session_state.produtos = carregar_produtos()
                        st.rerun()
                        
                with c3:
                    if st.button("❌", key="del_{0}".format(item['id']), help="Remover item por completo"):
                        cursor.execute("DELETE FROM produtos WHERE id = ?", (item['id'],))
                        conn.commit()
                        st.session_state.produtos = carregar_produtos()
                        st.rerun()
