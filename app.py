import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Automotivo Pro",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# IDENTIDADE VISUAL
# =========================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #111211;
    color: #F2F2F0;
}

[data-testid="stHeader"] {
    background: rgba(17,18,17,0.95);
}

[data-testid="stSidebar"] {
    background: #191A19;
    border-right: 1px solid #303130;
}

[data-testid="stSidebar"] * {
    color: #EAEAE7;
}

.block-container {
    padding-top: 2.2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

h1, h2, h3 {
    color: #F4F4F1 !important;
    letter-spacing: -0.7px;
}

p, label, span {
    color: inherit;
}

.small-muted {
    color: #969994;
    font-size: 13px;
}

.brand {
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 3px;
    color: #FFFFFF;
}

.brand span {
    color: #92958F;
}

.hero {
    background: linear-gradient(120deg, #242624, #181918);
    border: 1px solid #363836;
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 25px;
}

.hero-label {
    font-size: 11px;
    letter-spacing: 3px;
    color: #A5A8A2;
    font-weight: 700;
}

.hero-title {
    font-size: 30px;
    line-height: 1.3;
    font-weight: 800;
    margin-top: 12px;
    color: #FFFFFF;
}

.hero-description {
    font-size: 14px;
    color: #B5B7B1;
    margin-top: 8px;
}

.metric-card {
    background: #1B1C1B;
    border: 1px solid #323432;
    border-radius: 12px;
    padding: 20px;
    min-height: 115px;
}

.metric-label {
    font-size: 12px;
    color: #A3A59F;
}

.metric-value {
    font-size: 27px;
    font-weight: 800;
    color: #F6F6F3;
    margin-top: 12px;
}

.vehicle-card {
    background: #1B1C1B;
    border: 1px solid #353735;
    border-radius: 13px;
    padding: 13px;
    margin-bottom: 10px;
}

.vehicle-name {
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    margin-top: 12px;
}

.vehicle-details {
    font-size: 12px;
    color: #A3A59F;
    margin-top: 6px;
}

.vehicle-price {
    font-size: 22px;
    font-weight: 800;
    color: #F5F5F2;
    margin-top: 16px;
}

.status {
    display: inline-block;
    border: 1px solid #454745;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 10px;
    color: #D7D9D3;
    margin-top: 10px;
}

div.stButton > button {
    background: #E9E9E5;
    color: #171817;
    border: 1px solid #E9E9E5;
    border-radius: 7px;
    font-weight: 700;
    min-height: 42px;
}

div.stButton > button:hover {
    background: #FFFFFF;
    color: #111211;
    border-color: #FFFFFF;
}

[data-testid="stMetric"] {
    background: #1B1C1B;
    border: 1px solid #323432;
    padding: 15px;
    border-radius: 10px;
}

[data-testid="stMetricLabel"] {
    color: #A3A59F;
}

[data-testid="stMetricValue"] {
    color: #F6F6F3;
}

input, textarea {
    background-color: #202120 !important;
}

hr {
    border-color: #333533;
}

.stSelectbox label,
.stTextInput label,
.stNumberInput label,
.stFileUploader label {
    color: #D9DAD5 !important;
}

</style>
""", unsafe_allow_html=True)


# =========================
# DADOS DA SESSÃO
# =========================

if "veiculos" not in st.session_state:
    st.session_state.veiculos = []

if "proximo_id" not in st.session_state:
    st.session_state.proximo_id = 1


def dinheiro(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def card_metrica(titulo, valor):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{titulo}</div>
            <div class="metric-value">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# MENU LATERAL
# =========================

with st.sidebar:
    st.markdown(
        '<div class="brand">AUTOMOTIVO <span>PRO</span></div>',
        unsafe_allow_html=True
    )

    st.caption("GESTÃO AUTOMOTIVA")
    st.divider()

    pagina = st.radio(
        "NAVEGAÇÃO",
        [
            "Visão geral",
            "Estoque de veículos",
            "Cadastrar veículo"
        ],
        label_visibility="visible"
    )

    st.divider()

    st.markdown(
        '<div class="small-muted">SISTEMA AUTOMOTIVO PRO</div>',
        unsafe_allow_html=True
    )

    st.caption("Versão inicial")


# =========================
# INDICADORES
# =========================

veiculos = st.session_state.veiculos

total = len(veiculos)

disponiveis = sum(
    v["situacao"] == "Disponível" for v in veiculos
)

reservados = sum(
    v["situacao"] == "Reservado" for v in veiculos
)

vendidos = sum(
    v["situacao"] == "Vendido" for v in veiculos
)

valor_estoque = sum(
    v["preco"] for v in veiculos
    if v["situacao"] != "Vendido"
)


# =========================
# VISÃO GERAL
# =========================

if pagina == "Visão geral":

    st.markdown("""
    <div class="hero">
        <div class="hero-label">PAINEL DE CONTROLE</div>
        <div class="hero-title">Sua operação.<br>Em um só lugar.</div>
        <div class="hero-description">
            Gerencie o estoque e acompanhe os veículos da sua loja.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Resumo da operação")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        card_metrica("TOTAL DE VEÍCULOS", total)

    with c2:
        card_metrica("DISPONÍVEIS", disponiveis)

    with c3:
        card_metrica("RESERVADOS", reservados)

    with c4:
        card_metrica("VENDIDOS", vendidos)

    st.write("")

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown("### Estoque da loja")
        st.caption("Valor anunciado dos veículos não vendidos.")

        st.markdown(
            f"""
            <div class="hero">
                <div class="hero-label">VALOR EM ESTOQUE</div>
                <div class="hero-title">{dinheiro(valor_estoque)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("### Acesso rápido")

        if st.button(
            "＋ Cadastrar veículo",
            use_container_width=True
        ):
            st.session_state.pagina_atalho = "Cadastrar veículo"
            st.rerun()

        if st.button(
            "⌕ Consultar estoque",
            use_container_width=True
        ):
            st.session_state.pagina_atalho = "Estoque de veículos"
            st.rerun()

    if "pagina_atalho" in st.session_state:
        destino = st.session_state.pop("pagina_atalho")
        st.info(
            f"Selecione '{destino}' no menu lateral para continuar."
        )

    st.divider()

    st.subheader("Últimos veículos cadastrados")

    if not veiculos:
        st.info(
            "Seu estoque está vazio. Cadastre o primeiro veículo "
            "para começar."
        )
    else:
        for v in reversed(veiculos[-3:]):
            a, b, c = st.columns([3, 2, 2])

            a.write(f"**{v['marca']} {v['modelo']}**")
            b.write(dinheiro(v["preco"]))
            c.write(v["situacao"])


# =========================
# CADASTRO
# =========================

elif pagina == "Cadastrar veículo":

    st.markdown(
        '<div class="hero">'
        '<div class="hero-label">GESTÃO DE ESTOQUE</div>'
        '<div class="hero-title">Cadastrar veículo</div>'
        '<div class="hero-description">'
        'Adicione os dados do veículo para registrá-lo no estoque.'
        '</div></div>',
        unsafe_allow_html=True
    )

    with st.form("cadastro_veiculo", clear_on_submit=True):

        st.markdown("### Informações do veículo")

        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca *")
            modelo = st.text_input("Modelo *")
            ano = st.number_input(
                "Ano",
                min_value=1950,
                max_value=2100,
                value=2022
            )

        with col2:
            quilometragem = st.number_input(
                "Quilometragem",
                min_value=0,
                value=0,
                step=1000
            )

            preco = st.number_input(
                "Preço de venda (R$) *",
                min_value=0.0,
                value=0.0,
                step=500.0
            )

            situacao = st.selectbox(
                "Situação inicial",
                ["Disponível", "Reservado", "Vendido"]
            )

        foto = st.file_uploader(
            "Foto principal do veículo",
            type=["jpg", "jpeg", "png", "webp"]
        )

        salvar = st.form_submit_button(
            "SALVAR VEÍCULO",
            use_container_width=True
        )

        if salvar:

            if not marca.strip() or not modelo.strip():
                st.error("Preencha a marca e o modelo.")

            elif preco <= 0:
                st.error("Informe um preço maior que zero.")

            else:
                st.session_state.veiculos.append({
                    "id": st.session_state.proximo_id,
                    "marca": marca.strip(),
                    "modelo": modelo.strip(),
                    "ano": int(ano),
                    "km": int(quilometragem),
                    "preco": float(preco),
                    "situacao": situacao,
                    "foto": foto.getvalue() if foto else None,
                    "data": datetime.now().strftime("%d/%m/%Y")
                })

                st.session_state.proximo_id += 1

                st.success("Veículo cadastrado com sucesso!")
                st.rerun()


# =========================
# ESTOQUE
# =========================

elif pagina == "Estoque de veículos":

    st.markdown(
        '<div class="hero">'
        '<div class="hero-label">INVENTÁRIO DA LOJA</div>'
        '<div class="hero-title">Estoque de veículos</div>'
        '<div class="hero-description">'
        'Pesquise, visualize e controle os veículos da concessionária.'
        '</div></div>',
        unsafe_allow_html=True
    )

    f1, f2, f3 = st.columns([2, 1, 1])

    with f1:
        pesquisa = st.text_input(
            "Pesquisar",
            placeholder="Marca ou modelo..."
        )

    with f2:
        filtro_situacao = st.selectbox(
            "Disponibilidade",
            ["Todos", "Disponível", "Reservado", "Vendido"]
        )

    with f3:
        ordenar = st.selectbox(
            "Ordenar por",
            ["Mais recentes", "Menor preço", "Maior preço"]
        )

    filtrados = []

    for v in st.session_state.veiculos:

        nome = f"{v['marca']} {v['modelo']}".lower()

        if pesquisa.lower() not in nome:
            continue

        if (
            filtro_situacao != "Todos"
            and v["situacao"] != filtro_situacao
        ):
            continue

        filtrados.append(v)

    if ordenar == "Menor preço":
        filtrados.sort(key=lambda v: v["preco"])

    elif ordenar == "Maior preço":
        filtrados.sort(
            key=lambda v: v["preco"],
            reverse=True
        )

    else:
        filtrados.sort(
            key=lambda v: v["id"],
            reverse=True
        )

    st.markdown(
        f'<div class="small-muted">{len(filtrados)} veículo(s) encontrado(s)</div>',
        unsafe_allow_html=True
    )

    st.write("")

    if not filtrados:
        st.info(
            "Nenhum veículo encontrado. "
            "Cadastre um veículo ou altere os filtros."
        )

    else:
        colunas = st.columns(3)

        for indice, v in enumerate(filtrados):

            with colunas[indice % 3]:

                with st.container(border=True):

                    if v["foto"]:
                        st.image(
                            v["foto"],
                            use_container_width=True
                        )
                    else:
                        st.markdown(
                            """
                            <div style="
                                height:150px;
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                background:#252725;
                                border-radius:8px;
                                font-size:42px;
                            ">🚘</div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.markdown(
                        f'<div class="vehicle-name">'
                        f'{v["marca"]} {v["modelo"]}</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="vehicle-details">'
                        f'{v["ano"]} &nbsp; · &nbsp; '
                        f'{v["km"]:,} km'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="vehicle-price">'
                        f'{dinheiro(v["preco"])}</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="status">'
                        f'{v["situacao"].upper()}</div>',
                        unsafe_allow_html=True
                    )

                    st.write("")

                    with st.expander("Gerenciar veículo"):

                        nova_situacao = st.selectbox(
                            "Situação",
                            ["Disponível", "Reservado", "Vendido"],
                            index=[
                                "Disponível",
                                "Reservado",
                                "Vendido"
                            ].index(v["situacao"]),
                            key=f"status_{v['id']}"
                        )

                        if st.button(
                            "Atualizar situação",
                            key=f"atualizar_{v['id']}",
                            use_container_width=True
                        ):
                            v["situacao"] = nova_situacao
                            st.rerun()

                        if st.button(
                            "Excluir veículo",
                            key=f"excluir_{v['id']}",
                            use_container_width=True
                        ):
                            st.session_state.veiculos = [
                                item
                                for item in st.session_state.veiculos
                                if item["id"] != v["id"]
                            ]
                            st.rerun()
