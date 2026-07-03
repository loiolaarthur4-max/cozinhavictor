with col1:
    is_editing = st.session_state.edit_data is not None
    st.header("✏️ Editar Produto" if is_editing else "📥 Cadastrar Produto")
    
    d = st.session_state.edit_data if is_editing else {}

    # Histórico de Nomes
    st.subheader("Nome do Produto")
    opcoes_nome = [""] + get_historico("nome")
    sel_nome = st.selectbox("Selecionar do Histórico (Nome)", opcoes_nome)
    nome_f = st.text_input("Ou digitar NOVO nome:", value=d.get("nome", "") if is_editing else "")
    nome_final = nome_f if nome_f else sel_nome
    
    # Histórico de Marcas
    st.subheader("Marca")
    opcoes_marca = [""] + get_historico("marca")
    sel_marca = st.selectbox("Selecionar do Histórico (Marca)", opcoes_marca)
    marca_f = st.text_input("Ou digitar NOVA marca:", value=d.get("marca", "") if is_editing else "")
    marca_final = marca_f if marca_f else sel_marca
    
    locais = ["Geladeira da Cozinha", "Freezer Branco", "Geladeira Red Bull", "Geladeira Grande"]
    local_f = st.selectbox("Local", locais, index=locais.index(d["local"]) if is_editing and d["local"] in locais else 0)
    qtd_f = st.number_input("Quantidade", value=float(d.get("quantidade", 1.0)))
    
    opcoes_unidade = ["Kg", "g", "L", "mL"]
    unidade_atual = d.get("unidade", "Kg")
    idx_unid = opcoes_unidade.index(unidade_atual) if is_editing and unidade_atual in opcoes_unidade else 0
    unid_f = st.selectbox("Unidade", opcoes_unidade, index=idx_unid)
    
    peso_f = st.number_input("Peso/Volume", value=float(d.get("peso", 0.0)))
    data_f = st.date_input("Validade", value=d["validade"] if is_editing else date.today())
