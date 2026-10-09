import streamlit as st

st.set_page_config(page_title="Sistema Automotivo Pro", page_icon="🚗")

st.title("Sistema Automotivo Pro 🚗")
st.write("O sistema está funcionando!")

pagina = st.sidebar.radio("Menu", ["Painel", "Veículos", "Vendas"])

if pagina == "Painel":
st.header("Painel de controle")
st.write("Bem-vindo!")

elif pagina == "Veículos":
st.header("Cadastro de veículos")
marca = st.text_input("Marca")
modelo = st.text_input("Modelo")

```
if st.button("Cadastrar"):
    st.success("Botão funcionando!")
```

elif pagina == "Vendas":
st.header("Controle de vendas")
st.write("Área de vendas")
