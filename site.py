import streamlit as st
from datetime import datetime, date
import sqlite3
import time

# Configuração da página do site
st.set_page_config(page_title="Controle de Validade - Cozinha", page_icon="🍳", layout="wide")

# Título principal do Site
st.title("🍳 Sistema de Controle da Cozinha")
st.write("Sistema permanente ativo. Aguardando comandos do cozinheiro **Arthur**.")

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

# 2. UPGRADES DE COLUNAS
colunas_para_adicionar = [
    ("marca", "TEXT"),
    ("quantidade", "REAL DEFAULT 1.0"),
    ("peso", "REAL DEFAULT 0.0"),
    ("unidade", "TEXT DEFAULT 'Kg'")
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
    cursor.execute("SELECT id, nome, marca, local, validade, quantidade, peso, unidade FROM produtos")
    linhas = cursor.fetchall()
    lista_produtos = []
    for linha in linhas:
        marca_produto = linha[2] if linha[2] else ""
        qtd_produto = linha[5] if (len(linha) > 5 and linha[5] is not None) else 1.0
        peso_produto = linha[6] if (len(linha) > 6 and linha[6] is not None) else 0.0
        unidade_produto = linha[7] if (len(linha) > 7 and linha[7]) else "Kg"
        
        lista_produtos.append({
            "id": linha[0],
            "nome": linha[1],
            "marca": marca_produto,
            "local": linha[3],
            "validade": datetime.strptime(linha[4], "%Y-%m-%d").date(),
            "quantidade": qtd_produto,
            "peso": peso_produto,
            "unidade": unity_var := unidade_produto
        })
    return lista_produtos

def carregar_historico_nomes():
    cursor.execute("SELECT item_nome FROM historico ORDER BY item_nome ASC")
    return [linha[0] for linha in cursor.fetchall()]

def carregar_historico_marcas():
    # HISTÓRICO CORRIGIDO: Removido o bug que travava a listagem de marcas
    cursor.execute("SELECT DISTINCT item_marca FROM historico WHERE item_marca IS NOT NULL AND item_marca != '' ORDER BY item_marca ASC")
    return [linha[0] for linha in cursor.fetchall()]

if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_produtos()

if "backup_produtos" not in st.session_state:
    st.session_state.backup_produtos = None
if "tempo_limpeza" not in st.session_state:
    st.session_state.tempo_limpeza = 0

# Controle do sistema de Edição em memória
if "id_edicao" not in st.session_state:
    st.session_state.id_edicao = None
if "valores_edicao" not in st.session_state:
    st.session_state.valores_edicao = {}

# Divisão em duas colunas principais
col1, col2 = st.columns([1.1, 1.7])

# COLUNA 1: Cadastro Combinado e Formulário de Edição
with col1:
    if st.session_state.id_edicao is not None:
        st.header("✏️ Editar Produto")
        valores = st.session_state.valores_edicao
    else:
        st.header("📥 Cadastrar Novo Produto")
        valores = {"nome": "", "marca": "", "local": "Geladeira da Cozinha", "quantidade": 1.0, "unidade": "Kg", "peso": 0.0, "validade": date.today()}
    
    lista_sugestoes_nome = carregar_historico_nomes()
    lista_sugestoes_marca = carregar_historico_marcas()
    
    # Nome do produto
    idx_nome = lista_sugestoes_nome.index(valores["nome"]) + 1 if valores["nome"] in lista_sugestoes_nome else 0
    nome_item = st.selectbox("Nome do Alimento (Histórico):", options=[""] + lista_sugestoes_nome, index=idx_nome, key="sel_prod")
    nome_novo = st.text_input("Ou digite um NOVO nome:", value=valores["nome"] if idx_nome == 0 else "", key="txt_prod")
    nome_final = nome_novo.strip() if nome_novo else nome_item
    
    # Marca do produto
    idx_marca = lista_sugestoes_marca.index(valores["marca"]) + 1 if valores["marca"] in lista_sugestoes_marca else 0
    st.write(f"*(Marcas salvas: {len(lista_sugestoes_marca)})*")
    marca_item = st.selectbox("Marca (Histórico):", options=[""] + lista_sugestoes_marca, index=idx_marca, key="mar_prod")
    marca_nova = st.text_input("Ou digite uma NOVA marca:", value=valores["marca"] if idx_marca == 0 else "", key="txt_mar_prod")
    marca_final = marca_nova.strip() if marca_nova else marca_item

    # Locais Atualizados conforme seu pedido
    lista_locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    idx_local = lista_locais.index(valores["local"]) if valores["local"] in lista_locais else 0
    local_armazenamento = st.selectbox("Onde guardar?", lista_locais, index=idx_local, key="loc_prod")
    
    st.write("---")
    st.subheader("Medidas do Produto")
    
    # Quantidade de itens
    qtd_itens = st.number_input("Quantidade de Unidades/Pacotes:", min_value=1.0, value=float(valores["quantidade"]), step=1.0, format="%.0f", key="input_qtd_geral")
    
    # Seleção de unidade com as novas opções L e mL
    lista_unidades = ["Kg", "g", "L", "mL"]
    idx_unidade = lista_unidades.index(valores["unidade"]) if valores["unidade"] in lista_unidades else 0
    
    c_tipo, c_valor = st.columns([1.1, 1.9])
    with c_tipo:
        tipo_peso = st.radio("Métrica:", lista_unidades, index=idx_unidade, horizontal=True, key="tipo_peso_sistema")
    with c_valor:
        # Mudança do texto para Volume/Peso conforme seu pedido
        if tipo_peso in ["Kg", "L"]:
            peso_item = st.number_input("Volume/Peso por pacote:", min_value=0.0, value=float(valores["peso"]), step=0.1, format="%.2f", key="peso_decimal")
        else:
            peso_item = st.number_input("Volume/Peso por pacote:", min_value=0.0, value=float(valores["peso"]), step=50.0, format="%.0f", key="peso_inteiro")
        
    idx_data = valores["validade"] if valores["validade"] >= date.today() else date.today()
    data_validade = st.date_input("Data de Validade:", min_value=date.today(), value=idx_data, key="data_prod")
    
    # Botões dinâmicos de salvar ou atualizar
    if st.session_state.id_edicao is not None:
        c_salvar, c_cancelar = st.columns(2)
        with c_salvar:
            if st.button("💾 Atualizar Produto", use_container_width=True, key="btn_atualizar"):
                if nome_final:
                    data_texto = data_validade.strftime("%Y-%m-%d")
                    cursor.execute(
                        "UPDATE produtos SET nome=?, marca=?, local=?, validade=?, quantidade=?, peso=?, unidade=? WHERE id=?",
                        (nome_final, marca_final, local_armazenamento, data_texto, qtd_itens, peso_item, tipo_peso, st.session_state.id_edicao)
                    )
                    cursor.execute("INSERT OR IGNORE INTO historico (item_nome, item_marca) VALUES (?, ?)", (nome_final, marca_final))
                    conn.commit()
                    st.session_state.produtos = carregar_produtos()
                    st.session_state.id_edicao = None
                    st.success("✅ Produto atualizado!")
                    st.rerun()
        with c_cancelar:
            if st.button("❌ Cancelar", use_container_width=True, key="btn_cancelar_edit"):
                st.session_state.id_edicao = None
                st.rerun()
    else:
        if st.button("🚀 Adicionar ao Estoque", use_container_width=True, key="btn_salvar_tudo"):
            if nome_final:
                data_texto = data_validade.strftime("%Y-%m-%d")
                cursor.execute(
                    "INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (nome_final, marca_final, local_armazenamento, data_texto, qtd_itens, peso_item, tipo_peso)
                )
                cursor.execute("INSERT OR IGNORE INTO historico (item_nome, item_marca) VALUES (?, ?)", (nome_final, marca_final))
                conn.commit()
                st.session_state.produtos = carregar_produtos()
                st.success(f"🟢 {nome_final} adicionado!")
                st.rerun()
            else:
                st.error("⚠️ Digite ou selecione o nome do produto.")

# COLUNA 2: Painel de Estoque e Visores com Botão de Editar
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
                        "INSERT INTO produtos (nome, marca, local, validade, quantidade, peso, unidade) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                        (item["nome"], item["marca"], item["local"], item["validade"].strftime("%Y-%m-%d"), item["quantidade"], item["peso"], item["unidade"])
                    )
                conn.commit()
                st.session_state.produtos = carregar_produtos()
                st.session_state.backup_produtos = None
                st.success("✅ Estoque recuperado!")
                st.rerun()
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.backup_produtos = None
            st.rerun()

    if len(st.session_state.produtos) == 0 and st.session_state.backup_produtos is None:
        st.info("O estoque está completamente vazio. Arthur pode começar a enviar os produtos!")
    
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
            
            qtd_card = item['quantidade']
            peso_card = item['peso']
            unidade_card = item['unidade']
            
            # Formatação do visor combinando volumes, pesos e as novas métricas
            if peso_card > 0:
                if unidade_card in ["Kg", "L"]:
                    texto_medida = "{:.0f} Unid. x {:.2f} {}".format(qtd_card, peso_card, unidade_card)
                else:
                    texto_medida = "{:.0f} Unid. x {:.0f} {}".format(qtd_card, peso_card, unidade_card)
            else:
                texto_medida = "{:.0f} Unidades".format(qtd_card)
            
            card_col, control_col = st.columns([3.8, 1.2])
            
            with card_col:
                html_card = (
                    '<div style="padding: 12px; border-radius: 8px; border-left: 6px solid ' + cor_alarme + '; '
                    'background-color: ' + cor_fundo + '; margin-bottom: 12px; color: #1e293b; font-family: sans-serif;">'
                    '<span style="font-size: 12pt; font-weight: bold;">' + str(item['nome']) + texto_marca + '</span> <br>'
                    '<span style="font-size: 10.5pt; color: #0f172a;">📦 Estoque: <b>' + texto_medida + '</b></span><br>'
                    '<span style="font-size: 9.5pt;">📍 Local: <b>' + str(item['local']) + '</b> | Validade: ' + item['validade'].strftime('%d/%m/%Y') + '</span><br>'
                    '<span style="font-size: 10.5pt; font-weight: bold; color: ' + cor_alarme + ';">' + status_texto + '</span>'
                    '</div>'
                )
                st.html(html_card)
                
            with control_col:
                st.write("") 
                c_edit, c_del = st.columns(2)
                
                with c_edit:
                    # Novo Botão de Editar
                    if st.button("✏️", key="edit_{0}".format(item['id']), help="Editar informações deste produto"):
                        st.session_state.id_edicao = item['id']
                        st.session_state.valores_edicao = item.copy()
                        st.rerun()
                        
                with c_del:
                    if st.button("❌", key="del_{0}".format(item['id']), help="Remover item por completo"):
                        cursor.execute("DELETE FROM produtos WHERE id = ?", (item['id'],))
                        conn.commit()
                        if st.session_state.id_edicao == item['id']:
                            st.session_state.id_edicao = None
                        st.session_state.produtos = carregar_produtos()
                        st.rerun()
