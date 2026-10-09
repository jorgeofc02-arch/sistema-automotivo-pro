import streamlit as st

st.set_page_config(page_title="Sistema Automotivo Pro", page_icon="🚗", layout="wide")

st.title("🚗 Sistema Automotivo Pro")
st.caption("Gestão inteligente para lojas e concessionárias")

st.sidebar.title("Menu")

pagina = st.sidebar.radio(
"Navegação",
["Painel", "Cadastrar veículo", "Estoque", "Vendas", "Financeiro"]
)

if pagina == "Painel":
st.header("Painel de controle")
st.info("Bem-vindo ao seu sistema de gestão automotiva!")

```
col1, col2, col3 = st.columns(3)
col1.metric("Veículos em estoque", 0)
col2.metric("Vendas realizadas", 0)
col3.metric("Lucro total", "R$ 0,00")
```

elif pagina == "Cadastrar veículo":
st.header("Cadastrar veículo")

```
with st.form("form_veiculo"):
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    ano = st.number_input("Ano", min_value=1950, max_value=2100, value=2020)
    preco_compra = st.number_input("Preço de compra (R$)", min_value=0.0)
    preco_venda = st.number_input("Preço de venda (R$)", min_value=0.0)
    enviar = st.form_submit_button("Cadastrar veículo")

if enviar:
    if marca.strip() and modelo.strip():
        st.success(f"Veículo preenchido: {marca} {modelo}, ano {ano}.")
        st.warning("O cadastro ainda não fica salvo permanentemente.")
    else:
        st.error("Preencha a marca e o modelo.")
```

elif pagina == "Estoque":
st.header("📦 Estoque de veículos")
st.info("Vamos conectar o estoque ao banco de dados.")

elif pagina == "Vendas":
st.header("💰 Controle de vendas")
st.info("Vamos implementar o registro de vendas.")

elif pagina == "Financeiro":
st.header("📊 Financeiro")
st.info("Vamos implementar os relatórios financeiros.")
