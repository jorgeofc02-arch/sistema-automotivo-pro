import streamlit as st

st.set_page_config(page_title="Sistema Automotivo Pro", page_icon="🚗")

st.title("🚗 Sistema Automotivo Pro")
st.subheader("Sistema de gestão para concessionárias")

st.sidebar.title("Menu")
st.sidebar.write("Painel de controle")

st.metric("Veículos em estoque", 0)
st.metric("Vendas realizadas", 0)
st.metric("Lucro total", "R$ 0,00")

st.header("Cadastro de veículos")

marca = st.text_input("Marca do veículo")
modelo = st.text_input("Modelo do veículo")
ano = st.number_input("Ano", min_value=1950, max_value=2100, value=2020)

st.write("Confira os dados preenchidos:")
st.write("Marca:", marca)
st.write("Modelo:", modelo)
st.write("Ano:", ano)
