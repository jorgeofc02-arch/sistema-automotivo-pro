import streamlit as st

st.set_page_config(
    page_title="Sistema Automotivo Pro",
    page_icon="🚗",
    layout="wide"
)

# ESTILO VISUAL
st.markdown("""
<style>
.stApp {
    background-color: #f2f2f0;
    color: #222222;
}
[data-testid="stSidebar"] {
    background-color: #202020;
}
[data-testid="stSidebar"] * {
    color: #f5f5f5;
}
h1, h2, h3 {
    color: #202020;
}
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #dededb;
    padding: 18px;
    border-radius: 12px;
}
.stButton button {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# DADOS TEMPORÁRIOS
if "veiculos" not in st.session_state:
    st.session_state.veiculos = []

if "proximo_id" not in st.session_state:
    st.session_state.proximo_id = 1

# MENU
st.sidebar.title("🚗 Sistema Automotivo Pro")
st.sidebar.caption("GESTÃO AUTOMOTIVA")

pagina = st.sidebar.radio(
    "MENU PRINCIPAL",
    [
        "Dashboard",
        "Estoque de veículos",
        "Cadastrar veículo"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Versão inicial do sistema")

# DASHBOARD
if pagina == "Dashboard":
    st.title("Painel de controle")
    st.write("Visão geral da sua concessionária.")

    total = len(st.session_state.veiculos)

    disponiveis = sum(
        v["situacao"] == "Disponível"
        for v in st.session_state.veiculos
    )

    reservados = sum(
        v["situacao"] == "Reservado"
        for v in st.session_state.veiculos
    )

    vendidos = sum(
        v["situacao"] == "Vendido"
        for v in st.session_state.veiculos
    )

    valor_estoque = sum(
        v["preco"]
        for v in st.session_state.veiculos
        if v["situacao"] != "Vendido"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total de veículos", total)
    c2.metric("Disponíveis", disponiveis)
    c3.metric("Reservados", reservados)
    c4.metric("Vendidos", vendidos)

    st.divider()

    st.subheader("Valor anunciado em estoque")
    st.markdown(
        f"## R$ {valor_estoque:,.2f}".replace(",", "X")
        .replace(".", ",").replace("X", ".")
    )

    st.info(
        "Cadastre os veículos da loja para começar "
        "a acompanhar seu estoque."
    )

# CADASTRO
elif pagina == "Cadastrar veículo":
    st.title("Cadastrar veículo")
    st.write("Preencha os dados do veículo.")

    with st.form("form_cadastro", clear_on_submit=True):
        c1, c2 = st.columns(2)

        with c1:
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            ano = st.number_input(
                "Ano",
                min_value=1950,
                max_value=2100,
                value=2020
            )
            quilometragem = st.number_input(
                "Quilometragem",
                min_value=0,
                value=0,
                step=1000
            )

        with c2:
            preco = st.number_input(
                "Preço de venda (R$)",
                min_value=0.0,
                value=0.0,
                step=500.0
            )

            situacao = st.selectbox(
                "Situação",
                ["Disponível", "Reservado", "Vendido"]
            )

            foto = st.file_uploader(
                "Foto do veículo",
                type=["jpg", "jpeg", "png", "webp"]
            )

        salvar = st.form_submit_button(
            "Cadastrar veículo",
            use_container_width=True
        )

        if salvar:
            if not marca.strip() or not modelo.strip():
                st.error("Preencha a marca e o modelo.")
            elif preco <= 0:
                st.error("Informe um preço maior que zero.")
            else:
                imagem = foto.getvalue() if foto else None

                st.session_state.veiculos.append({
                    "id": st.session_state.proximo_id,
                    "marca": marca.strip(),
                    "modelo": modelo.strip(),
                    "ano": int(ano),
                    "km": int(quilometragem),
                    "preco": float(preco),
                    "situacao": situacao,
                    "foto": imagem
                })

                st.session_state.proximo_id += 1

                st.success("Veículo cadastrado!")
                st.rerun()

# ESTOQUE
elif pagina == "Estoque de veículos":
    st.title("🚘 Carros disponíveis")
    st.write("Consulte e gerencie os veículos da concessionária.")

    veiculos = st.session_state.veiculos

    c1, c2 = st.columns([2, 1])

    with c1:
        pesquisa = st.text_input(
            "Pesquisar veículo",
            placeholder="Digite a marca ou o modelo..."
        )

    with c2:
        filtro = st.selectbox(
            "Filtrar por situação",
            ["Todos", "Disponível", "Reservado", "Vendido"]
        )

    filtrados = []

    for v in veiculos:
        nome = f"{v['marca']} {v['modelo']}".lower()

        corresponde_nome = pesquisa.lower() in nome
        corresponde_situacao = (
            filtro == "Todos" or v["situacao"] == filtro
        )

        if corresponde_nome and corresponde_situacao:
            filtrados.append(v)

    st.caption(f"{len(filtrados)} veículo(s) encontrado(s)")
    st.divider()

    if not filtrados:
        st.info(
            "Nenhum veículo encontrado. "
            "Cadastre um veículo ou altere os filtros."
        )

    for v in filtrados:
        with st.container(border=True):
            foto_col, dados_col = st.columns([1, 2])

            with foto_col:
                if v["foto"]:
                    st.image(v["foto"], use_container_width=True)
                else:
                    st.markdown("### 🚗")
                    st.caption("Sem foto cadastrada")

            with dados_col:
                st.subheader(f"{v['marca']} {v['modelo']}")

                st.markdown(
                    f"**Preço:** R$ {v['preco']:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

                st.write(f"**Ano:** {v['ano']}")
                st.write(f"**Quilometragem:** {v['km']:,} km")
                st.write(f"**Situação:** {v['situacao']}")

                a, b = st.columns(2)

                with a:
                    nova_situacao = st.selectbox(
                        "Alterar situação",
                        ["Disponível", "Reservado", "Vendido"],
                        index=[
                            "Disponível", "Reservado", "Vendido"
                        ].index(v["situacao"]),
                        key=f"situacao_{v['id']}"
                    )

                    if nova_situacao != v["situacao"]:
                        v["situacao"] = nova_situacao
                        st.rerun()

                with b:
                    st.write("")
                    if st.button(
                        "Excluir veículo",
                        key=f"excluir_{v['id']}"
                    ):
                        st.session_state.veiculos = [
                            item for item in st.session_state.veiculos
                            if item["id"] != v["id"]
                        ]
                        st.rerun()
