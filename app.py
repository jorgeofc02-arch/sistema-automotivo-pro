import streamlit as st
import pandas as pd
import uuid
from supabase import create_client
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO
# ==========================================

st.set_page_config(
    page_title="Sistema Automotivo Pro",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #0b0d12;
        color: #f1f5f9;
    }

    section[data-testid="stSidebar"] {
        background: #10131a;
        border-right: 1px solid #242a36;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    .hero {
        background: linear-gradient(135deg, #171c27, #10131a);
        border: 1px solid #293140;
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 28px;
    }

    .hero h1 {
        color: #ffffff;
        font-size: 34px;
        font-weight: 800;
        margin: 0;
    }

    .hero p {
        color: #9ca8ba;
        margin-top: 10px;
    }

    .metric-card {
        background: #141821;
        border: 1px solid #293140;
        border-radius: 16px;
        padding: 22px;
        min-height: 125px;
    }

    .metric-label {
        color: #9ca8ba;
        font-size: 13px;
        margin-bottom: 12px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 27px;
        font-weight: 800;
    }

    .section-title {
        color: #ffffff;
        font-size: 23px;
        font-weight: 750;
        margin: 28px 0 18px 0;
    }

    .vehicle-card {
        background: #141821;
        border: 1px solid #293140;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .vehicle-name {
        color: #ffffff;
        font-size: 19px;
        font-weight: 750;
    }

    .vehicle-info {
        color: #9ca8ba;
        font-size: 13px;
        margin-top: 7px;
    }

    .vehicle-price {
        color: #58d6a0;
        font-size: 22px;
        font-weight: 800;
        margin-top: 14px;
    }

    div.stButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
    }

    div[data-testid="stForm"] {
        background: #141821;
        border: 1px solid #293140;
        border-radius: 16px;
        padding: 22px;
    }

    h1, h2, h3 {
        color: #ffffff;
    }

    label {
        color: #d5dbe5 !important;
    }

    .stTextInput input, .stNumberInput input {
        background: #0f1219;
    }

    .footer {
        text-align: center;
        color: #697588;
        font-size: 12px;
        padding-top: 35px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# CONEXÃO COM O SUPABASE
# ==========================================

@st.cache_resource
def conectar_supabase():
    url = st.secrets["supabase"]["url"]
    chave = st.secrets["supabase"]["secret_key"]
    return create_client(url, chave)


try:
    supabase = conectar_supabase()
except Exception as erro:
    st.error("Não foi possível conectar ao Supabase.")
    st.info(
        "Confira os Secrets do Streamlit. "
        "A seção [supabase] precisa conter url e secret_key."
    )
    st.stop()


# ==========================================
# CONCESSIONÁRIA DE TESTE
# ==========================================

@st.cache_resource
def obter_concessionaria():
    resultado = (
        supabase.table("concessionarias")
        .select("id, nome")
        .order("criado_em")
        .limit(1)
        .execute()
    )

    if resultado.data:
        return resultado.data[0]

    criada = (
        supabase.table("concessionarias")
        .insert({"nome": "Minha Concessionária"})
        .execute()
    )

    if not criada.data:
        raise RuntimeError("Não foi possível criar a concessionária.")

    return criada.data[0]


try:
    concessionaria = obter_concessionaria()
    concessionaria_id = concessionaria["id"]
except Exception as erro:
    st.error("Erro ao preparar a concessionária de teste.")
    st.code(str(erro))
    st.stop()


# ==========================================
# FUNÇÕES
# ==========================================

def buscar_veiculos():
    resposta = (
        supabase.table("veiculos")
        .select("*")
        .eq("concessionaria_id", concessionaria_id)
        .order("criado_em", desc=True)
        .execute()
    )
    return resposta.data or []


def formatar_moeda(valor):
    valor_formatado = f"{float(valor):,.2f}"
    valor_formatado = valor_formatado.replace(",", "X")
    valor_formatado = valor_formatado.replace(".", ",")
    valor_formatado = valor_formatado.replace("X", ".")
    return f"R$ {valor_formatado}"


def obter_url_foto(caminho):
    if not caminho:
        return None

    try:
        resposta = (
            supabase.storage
            .from_("fotos-veiculos")
            .create_signed_url(caminho, 3600)
        )

        if isinstance(resposta, dict):
            return resposta.get("signedURL") or resposta.get("signedUrl")

        return None
    except Exception:
        return None


# ==========================================
# MENU LATERAL
# ==========================================

with st.sidebar:
    st.markdown("## 🚘 AUTO PRO")
    st.caption("GESTÃO AUTOMOTIVA")

    st.divider()
pagina = st.radio(
    "MENU PRINCIPAL",
    [
        "Dashboard",
        "Estoque de veículos",
        "Editar veículo",
        "Cadastrar veículo"
    ],
    label_visibility="visible"
)

    st.divider()

    st.markdown("### 🏢 Concessionária")
    st.write(concessionaria["nome"])

    st.caption("Versão de desenvolvimento")
    st.caption("Dados armazenados no Supabase")


# ==========================================
# CARREGAR DADOS
# ==========================================

try:
    veiculos = buscar_veiculos()
except Exception as erro:
    st.error("Não foi possível carregar os veículos.")
    st.code(str(erro))
    st.stop()


# ==========================================
# DASHBOARD
# ==========================================

if pagina == "Dashboard":

    st.markdown("""
    <div class="hero">
        <h1>Sistema Automotivo Pro</h1>
        <p>Controle seu estoque e acompanhe seus veículos em um só lugar.</p>
    </div>
    """, unsafe_allow_html=True)

    total = len(veiculos)
    disponiveis = sum(
        1 for v in veiculos if v["status"] == "Disponível"
    )
    reservados = sum(
        1 for v in veiculos if v["status"] == "Reservado"
    )
    vendidos = sum(
        1 for v in veiculos if v["status"] == "Vendido"
    )

    valor_estoque = sum(
        float(v["preco"])
        for v in veiculos
        if v["status"] != "Vendido"
    )

    col1, col2, col3, col4 = st.columns(4)

    metricas = [
        (col1, "TOTAL DE VEÍCULOS", total),
        (col2, "DISPONÍVEIS", disponiveis),
        (col3, "RESERVADOS", reservados),
        (col4, "VENDIDOS", vendidos),
    ]

    for coluna, titulo, valor in metricas:
        with coluna:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{titulo}</div>
                    <div class="metric-value">{valor}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown(
        '<div class="section-title">Visão geral do estoque</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">VALOR DO ESTOQUE NÃO VENDIDO</div>
            <div class="metric-value">{formatar_moeda(valor_estoque)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">Veículos adicionados recentemente</div>',
        unsafe_allow_html=True
    )

    if not veiculos:
        st.info(
            "Seu estoque ainda está vazio. "
            "Acesse 'Cadastrar veículo' para adicionar o primeiro."
        )
    else:
        for veiculo in veiculos[:5]:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(
                        f"### {veiculo['marca']} {veiculo['modelo']}"
                    )
                    st.caption(
                        f"Ano {veiculo['ano']} · "
                        f"{veiculo['quilometragem']:,} km · "
                        f"Status: {veiculo['status']}"
                    )

                with col2:
                    st.markdown(
                        f"### {formatar_moeda(veiculo['preco'])}"
                    )


# ==========================================
# ESTOQUE
# ==========================================

elif pagina == "Estoque de veículos":

    st.markdown("## Estoque de veículos")
    st.caption("Consulte os veículos cadastrados no banco de dados.")

    pesquisa = st.text_input(
        "🔎 Pesquisar por marca ou modelo",
        placeholder="Ex.: Toyota, Corolla, Honda..."
    )

    filtro_status = st.selectbox(
        "Filtrar por status",
        ["Todos", "Disponível", "Reservado", "Vendido"]
    )

    filtrados = veiculos.copy()

    if pesquisa:
        filtrados = [
            v for v in filtrados
            if pesquisa.lower() in v["marca"].lower()
            or pesquisa.lower() in v["modelo"].lower()
        ]

    if filtro_status != "Todos":
        filtrados = [
            v for v in filtrados
            if v["status"] == filtro_status
        ]

    if not filtrados:
        st.info("Nenhum veículo encontrado com esses filtros.")

    for veiculo in filtrados:
        with st.container(border=True):
            foto_url = obter_url_foto(veiculo.get("foto_url"))

            col_foto, col_info, col_acoes = st.columns(
                [1, 2, 1]
            )

            with col_foto:
                if foto_url:
                    st.image(foto_url, use_container_width=True)
                else:
                    st.markdown("🚘")
                    st.caption("Sem foto")

            with col_info:
                st.markdown(
                    f"### {veiculo['marca']} {veiculo['modelo']}"
                )

                st.write(
                    f"**Ano:** {veiculo['ano']}  \n"
                    f"**Quilometragem:** "
                    f"{veiculo['quilometragem']:,} km  \n"
                    f"**Status:** {veiculo['status']}"
                )

                st.markdown(
                    f"## {formatar_moeda(veiculo['preco'])}"
                )

            with col_acoes:
                novo_status = st.selectbox(
                    "Status",
                    ["Disponível", "Reservado", "Vendido"],
                    index=[
                        "Disponível", "Reservado", "Vendido"
                    ].index(veiculo["status"]),
                    key=f"status_{veiculo['id']}"
                )

                if st.button(
                    "Atualizar status",
                    key=f"atualizar_{veiculo['id']}",
                    use_container_width=True
                ):
                    try:
                        (
                            supabase.table("veiculos")
                            .update({"status": novo_status})
                            .eq("id", veiculo["id"])
                            .eq("concessionaria_id", concessionaria_id)
                            .execute()
                        )

                        st.success("Status atualizado!")
                        st.rerun()

                    except Exception as erro:
                        st.error("Não foi possível atualizar.")
                        st.code(str(erro))

                confirmar_exclusao = st.checkbox(
                    "Confirmar exclusão",
                    key=f"confirmar_{veiculo['id']}"
                )

                if st.button(
                    "Excluir veículo",
                    key=f"excluir_{veiculo['id']}",
                    use_container_width=True
                ):
                    if not confirmar_exclusao:
                        st.warning(
                            "Marque 'Confirmar exclusão' antes de excluir."
                        )
                    else:
                        try:
                            if veiculo.get("foto_url"):
                                try:
                                    (
                                        supabase.storage
                                        .from_("fotos-veiculos")
                                        .remove([veiculo["foto_url"]])
                                    )
                                except Exception:
                                    pass

                            (
                                supabase.table("veiculos")
                                .delete()
                                .eq("id", veiculo["id"])
                                .eq("concessionaria_id", concessionaria_id)
                                .execute()
                            )

                            st.success("Veículo excluído.")
                            st.rerun()

                        except Exception as erro:
                            st.error("Não foi possível excluir o veículo.")
                            st.code(str(erro))


# ==========================================
# CADASTRAR VEÍCULO
# ==========================================

elif pagina == "Cadastrar veículo":

    st.markdown("## Cadastrar veículo")
    st.caption("Preencha os dados para adicionar um veículo ao estoque.")

    with st.form("form_cadastro_veiculo"):

        st.markdown("### Informações do veículo")

        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input(
                "Marca *",
                placeholder="Ex.: Toyota"
            )

            modelo = st.text_input(
                "Modelo *",
                placeholder="Ex.: Corolla XEi"
            )

            ano = st.number_input(
                "Ano *",
                min_value=1950,
                max_value=2035,
                value=2022,
                step=1
            )

        with col2:
            quilometragem = st.number_input(
                "Quilometragem *",
                min_value=0,
                max_value=2_000_000,
                value=0,
                step=1000
            )

            preco = st.number_input(
                "Preço de venda (R$) *",
                min_value=0.01,
                max_value=100_000_000.0,
                value=50000.0,
                step=1000.0
            )

            status = st.selectbox(
                "Status",
                ["Disponível", "Reservado", "Vendido"]
            )

        st.markdown("### Foto do veículo")

        foto = st.file_uploader(
            "Escolha uma imagem",
            type=["jpg", "jpeg", "png", "webp"],
            help="Formatos aceitos: JPG, PNG e WEBP. Máximo recomendado: 5 MB."
        )

        if foto is not None:
            st.image(foto, caption="Prévia da foto", use_container_width=True)

        enviado = st.form_submit_button(
            "💾 Salvar veículo",
            use_container_width=True
        )

        if enviado:

            if not marca.strip() or not modelo.strip():
                st.error("Preencha a marca e o modelo.")

            elif foto is not None and foto.size > 5 * 1024 * 1024:
                st.error("A imagem ultrapassa o limite de 5 MB.")

            else:
                caminho_foto = None

                try:
                    if foto is not None:
                        extensao = foto.name.rsplit(".", 1)[-1].lower()

                        if extensao == "jpeg":
                            extensao = "jpg"

                        nome_arquivo = (
                            f"{concessionaria_id}/"
                            f"{uuid.uuid4().hex}.{extensao}"
                        )

                        tipo_mime = {
                            "jpg": "image/jpeg",
                            "png": "image/png",
                            "webp": "image/webp"
                        }[extensao]

                        (
                            supabase.storage
                            .from_("fotos-veiculos")
                            .upload(
                                nome_arquivo,
                                foto.getvalue(),
                                {
                                    "content-type": tipo_mime,
                                    "upsert": "false"
                                }
                            )
                        )

                        caminho_foto = nome_arquivo

                    dados = {
                        "concessionaria_id": concessionaria_id,
                        "marca": marca.strip(),
                        "modelo": modelo.strip(),
                        "ano": int(ano),
                        "quilometragem": int(quilometragem),
                        "preco": float(preco),
                        "status": status,
                        "foto_url": caminho_foto
                    }

                    (
                        supabase.table("veiculos")
                        .insert(dados)
                        .execute()
                    )

                    st.success(
                        "Veículo cadastrado com sucesso! "
                        "Os dados foram enviados ao Supabase."
                    )

                    st.balloons()

                    st.cache_data.clear()
                    st.rerun()

                except Exception as erro:
                    st.error("Não foi possível salvar o veículo.")
                    st.warning(
                        "Confira a conexão, as permissões do banco "
                        "e as políticas de acesso ao Storage."
                    )
                    st.code(str(erro))


# ==========================================
# RODAPÉ
# ==========================================

st.markdown("""
<div class="footer">
    SISTEMA AUTOMOTIVO PRO · GESTÃO INTELIGENTE DE VEÍCULOS
</div>
""", unsafe_allow_html=True)
