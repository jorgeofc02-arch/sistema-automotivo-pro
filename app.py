import streamlit as st
import uuid
from supabase import create_client
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO
# ==========================================

st.set_page_config(
    page_title="Sistema Automotivo Pro",
    page_icon="🚘",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #0b0f19;
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background-color: #111827;
}
.block-container {
    padding-top: 2rem;
}
h1, h2, h3 {
    color: #f8fafc;
}
div[data-testid="stMetric"] {
    background: #151d2e;
    border: 1px solid #263248;
    padding: 18px;
    border-radius: 12px;
}
.stButton > button {
    border-radius: 8px;
    min-height: 42px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# SUPABASE
# ==========================================

@st.cache_resource
def conectar_supabase():
    url = st.secrets["supabase"]["url"]
    chave = st.secrets["supabase"].get(
        "secret_key",
        st.secrets["supabase"].get("key")
    )
    return create_client(url, chave)


try:
    supabase = conectar_supabase()
except Exception as erro:
    st.error("Não foi possível conectar ao banco de dados.")
    st.caption(str(erro))
    st.stop()


# ==========================================
# CONCESSIONÁRIA
# ==========================================

def obter_concessionaria():
    resultado = (
        supabase.table("concessionarias")
        .select("*")
        .limit(1)
        .execute()
    )

    if resultado.data:
        return resultado.data[0]["id"]

    nova = (
        supabase.table("concessionarias")
        .insert({"nome": "Minha Concessionária"})
        .execute()
    )

    return nova.data[0]["id"]


try:
    concessionaria_id = obter_concessionaria()
except Exception as erro:
    st.error("Erro ao acessar a concessionária no Supabase.")
    st.code(str(erro))
    st.stop()


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def buscar_veiculos():
    resultado = (
        supabase.table("veiculos")
        .select("*")
        .eq("concessionaria_id", concessionaria_id)
        .order("criado_em", desc=True)
        .execute()
    )
    return resultado.data or []


def moeda(valor):
    return f"R$ {float(valor or 0):,.2f}".replace(
        ",", "X"
    ).replace(".", ",").replace("X", ".")


def url_foto(caminho):
    if not caminho:
        return None

    try:
        resultado = (
            supabase.storage
            .from_("fotos-veiculos")
            .create_signed_url(caminho, 3600)
        )

        return (
            resultado.get("signedURL")
            or resultado.get("signedUrl")
        )
    except Exception:
        return None


def salvar_foto(arquivo):
    if arquivo is None:
        return None

    if arquivo.size > 5 * 1024 * 1024:
        raise ValueError("A imagem deve ter no máximo 5 MB.")

    extensao = arquivo.name.rsplit(".", 1)[-1].lower()

    tipos = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }

    if extensao not in tipos:
        raise ValueError("Formato inválido. Use JPG, PNG ou WEBP.")

    caminho = (
        f"{concessionaria_id}/"
        f"{uuid.uuid4().hex}.{extensao}"
    )

    supabase.storage.from_("fotos-veiculos").upload(
        caminho,
        arquivo.getvalue(),
        {
            "content-type": tipos[extensao],
            "upsert": "false",
        },
    )

    return caminho


def atualizar_veiculo(veiculo_id, dados):
    (
        supabase.table("veiculos")
        .update(dados)
        .eq("id", veiculo_id)
        .eq("concessionaria_id", concessionaria_id)
        .execute()
    )


# ==========================================
# MENU LATERAL
# ==========================================

with st.sidebar:
    st.markdown("# 🚘 AUTO PRO")
    st.caption("GESTÃO AUTOMOTIVA")
    st.divider()

    pagina = st.radio(
        "MENU PRINCIPAL",
        [
            "Dashboard",
            "Estoque de veículos",
            "Editar veículo",
            "Cadastrar veículo",
        ],
    )

    st.divider()
    st.caption("Sistema Automotivo Pro")
    st.caption("Versão de desenvolvimento")


# ==========================================
# DADOS
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
    st.title("Dashboard")
    st.caption("Visão geral da sua concessionária")

    total = len(veiculos)
    disponiveis = sum(
        1 for v in veiculos if v.get("status") == "Disponível"
    )
    reservados = sum(
        1 for v in veiculos if v.get("status") == "Reservado"
    )
    vendidos = sum(
        1 for v in veiculos if v.get("status") == "Vendido"
    )

    valor_estoque = sum(
        float(v.get("preco") or 0)
        for v in veiculos
        if v.get("status") != "Vendido"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("TOTAL DE VEÍCULOS", total)
    col2.metric("DISPONÍVEIS", disponiveis)
    col3.metric("RESERVADOS", reservados)
    col4.metric("VENDIDOS", vendidos)

    st.metric("VALOR DO ESTOQUE NÃO VENDIDO", moeda(valor_estoque))

    st.divider()
    st.subheader("Veículos recentes")

    if not veiculos:
        st.info("Seu estoque está vazio. Cadastre o primeiro veículo.")
    else:
        for veiculo in veiculos[:5]:
            st.markdown(
                f"**{veiculo['marca']} {veiculo['modelo']}** — "
                f"{veiculo['ano']} — {moeda(veiculo['preco'])}"
            )


# ==========================================
# ESTOQUE
# ==========================================

elif pagina == "Estoque de veículos":
    st.title("Estoque de veículos")

    busca = st.text_input(
        "Buscar veículo",
        placeholder="Digite marca ou modelo..."
    )

    filtro = st.selectbox(
        "Filtrar por status",
        ["Todos", "Disponível", "Reservado", "Vendido"]
    )

    filtrados = veiculos

    if busca:
        filtrados = [
            v for v in filtrados
            if busca.lower() in v.get("marca", "").lower()
            or busca.lower() in v.get("modelo", "").lower()
        ]

    if filtro != "Todos":
        filtrados = [
            v for v in filtrados
            if v.get("status") == filtro
        ]

    st.caption(f"{len(filtrados)} veículo(s) encontrado(s)")

    if not filtrados:
        st.info("Nenhum veículo encontrado.")
    else:
        for v in filtrados:
            with st.container(border=True):
                col_foto, col_info, col_status = st.columns(
                    [1, 2, 1]
                )

                with col_foto:
                    foto = url_foto(v.get("foto_url"))

                    if foto:
                        st.image(foto, use_container_width=True)
                    else:
                        st.markdown("📷 Sem foto")

                with col_info:
                    st.subheader(
                        f"{v.get('marca', '')} {v.get('modelo', '')}"
                    )
                    st.write(f"Ano: {v.get('ano', '-')}")
                    st.write(
                        f"Quilometragem: "
                        f"{int(v.get('quilometragem') or 0):,} km"
                        .replace(",", ".")
                    )
                    st.markdown(f"### {moeda(v.get('preco'))}")

                with col_status:
                    st.write("Status")
                    novo_status = st.selectbox(
                        "Status do veículo",
                        ["Disponível", "Reservado", "Vendido"],
                        index=[
                            "Disponível",
                            "Reservado",
                            "Vendido",
                        ].index(v.get("status", "Disponível")),
                        key=f"status_{v['id']}",
                        label_visibility="collapsed",
                    )

                    if st.button(
                        "Salvar status",
                        key=f"salvar_status_{v['id']}",
                        use_container_width=True,
                    ):
                        try:
                            atualizar_veiculo(
                                v["id"],
                                {"status": novo_status}
                            )
                            st.success("Status atualizado!")
                            st.rerun()
                        except Exception as erro:
                            st.error(f"Erro ao atualizar: {erro}")

                    if st.button(
                        "Excluir veículo",
                        key=f"excluir_{v['id']}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            f"confirmar_exclusao_{v['id']}"
                        ] = True

                    if st.session_state.get(
                        f"confirmar_exclusao_{v['id']}", False
                    ):
                        st.warning("Tem certeza que deseja excluir?")

                        sim, nao = st.columns(2)

                        if sim.button(
                            "Sim, excluir",
                            key=f"sim_{v['id']}",
                        ):
                            try:
                                (
                                    supabase.table("veiculos")
                                    .delete()
                                    .eq("id", v["id"])
                                    .eq(
                                        "concessionaria_id",
                                        concessionaria_id,
                                    )
                                    .execute()
                                )

                                st.session_state[
                                    f"confirmar_exclusao_{v['id']}"
                                ] = False

                                st.success("Veículo excluído.")
                                st.rerun()

                            except Exception as erro:
                                st.error(f"Erro ao excluir: {erro}")

                        if nao.button(
                            "Cancelar",
                            key=f"nao_{v['id']}",
                        ):
                            st.session_state[
                                f"confirmar_exclusao_{v['id']}"
                            ] = False
                            st.rerun()


# ==========================================
# EDITAR VEÍCULO
# ==========================================

elif pagina == "Editar veículo":
    st.title("Editar veículo")
    st.caption("Atualize as informações dos veículos cadastrados.")

    if not veiculos:
        st.info("Cadastre um veículo antes de tentar editá-lo.")
    else:
        opcoes = {
            (
                f"{v.get('marca', '')} "
                f"{v.get('modelo', '')} — "
                f"{v.get('ano', '')} — "
                f"{moeda(v.get('preco'))}"
            ): v
            for v in veiculos
        }

        selecionado = st.selectbox(
            "Selecione o veículo",
            list(opcoes.keys()),
        )

        v = opcoes[selecionado]

        st.divider()

        with st.form("form_editar_veiculo"):
            col1, col2 = st.columns(2)

            with col1:
                marca = st.text_input(
                    "Marca",
                    value=v.get("marca", ""),
                )
                modelo = st.text_input(
                    "Modelo",
                    value=v.get("modelo", ""),
                )
                ano = st.number_input(
                    "Ano",
                    min_value=1900,
                    max_value=2100,
                    value=int(v.get("ano") or 2020),
                )

            with col2:
                km = st.number_input(
                    "Quilometragem",
                    min_value=0,
                    value=int(v.get("quilometragem") or 0),
                )
                preco = st.number_input(
                    "Preço (R$)",
                    min_value=0.0,
                    value=float(v.get("preco") or 0),
                    step=500.0,
                )
                status = st.selectbox(
                    "Status",
                    ["Disponível", "Reservado", "Vendido"],
                    index=[
                        "Disponível",
                        "Reservado",
                        "Vendido",
                    ].index(v.get("status", "Disponível")),
                )

            foto_atual = url_foto(v.get("foto_url"))

            if foto_atual:
                st.image(
                    foto_atual,
                    caption="Foto atual",
                    width=300,
                )

            nova_foto = st.file_uploader(
                "Trocar foto (opcional)",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"foto_edicao_{v['id']}",
            )

            salvar = st.form_submit_button(
                "Salvar alterações",
                use_container_width=True,
            )

        if salvar:
            if not marca.strip() or not modelo.strip():
                st.error("Preencha a marca e o modelo.")
            else:
                try:
                    dados = {
                        "marca": marca.strip(),
                        "modelo": modelo.strip(),
                        "ano": int(ano),
                        "quilometragem": int(km),
                        "preco": float(preco),
                        "status": status,
                    }

                    if nova_foto is not None:
                        novo_caminho = salvar_foto(nova_foto)
                        dados["foto_url"] = novo_caminho

                    atualizar_veiculo(v["id"], dados)

                    st.success("Veículo atualizado com sucesso!")
                    st.rerun()

                except Exception as erro:
                    st.error("Não foi possível salvar as alterações.")
                    st.code(str(erro))


# ==========================================
# CADASTRAR VEÍCULO
# ==========================================

elif pagina == "Cadastrar veículo":
    st.title("Cadastrar veículo")
    st.caption("Adicione um veículo ao estoque da concessionária.")

    with st.form("form_cadastrar_veiculo"):
        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            ano = st.number_input(
                "Ano",
                min_value=1900,
                max_value=2100,
                value=2020,
            )

        with col2:
            km = st.number_input(
                "Quilometragem",
                min_value=0,
                value=0,
            )
            preco = st.number_input(
                "Preço (R$)",
                min_value=0.0,
                value=0.0,
                step=500.0,
            )
            status = st.selectbox(
                "Status",
                ["Disponível", "Reservado", "Vendido"],
            )

        foto = st.file_uploader(
            "Foto do veículo (opcional)",
            type=["jpg", "jpeg", "png", "webp"],
        )

        cadastrar = st.form_submit_button(
            "Cadastrar veículo",
            use_container_width=True,
        )

    if cadastrar:
        if not marca.strip() or not modelo.strip():
            st.error("Preencha a marca e o modelo.")
        else:
            try:
                caminho_foto = salvar_foto(foto) if foto else None

                dados = {
                    "concessionaria_id": concessionaria_id,
                    "marca": marca.strip(),
                    "modelo": modelo.strip(),
                    "ano": int(ano),
                    "quilometragem": int(km),
                    "preco": float(preco),
                    "status": status,
                    "foto_url": caminho_foto,
                }

                (
                    supabase.table("veiculos")
                    .insert(dados)
                    .execute()
                )

                st.success("Veículo cadastrado com sucesso!")
                st.rerun()

            except Exception as erro:
                st.error("Não foi possível cadastrar o veículo.")
                st.code(str(erro))


# ==========================================
# RODAPÉ
# ==========================================

st.divider()
st.caption("Sistema Automotivo Pro • Gestão de concessionárias")
