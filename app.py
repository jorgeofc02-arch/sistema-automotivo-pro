import streamlit as st
import uuid
from supabase import create_client

# ==================================================
# CONFIGURAÇÃO
# ==================================================

st.set_page_config(
    page_title="Auto Pro | Gestão Automotiva",
    page_icon="🚘",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background: #0b0f19;
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background: #111827;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}
h1, h2, h3 {
    color: #f8fafc;
}
p, label, span {
    letter-spacing: .1px;
}
[data-testid="stMetric"] {
    background: #151d2e;
    border: 1px solid #263248;
    border-radius: 12px;
    padding: 18px;
}
div.stButton > button,
div.stFormSubmitButton > button {
    border-radius: 8px;
    min-height: 42px;
}
small {
    color: #94a3b8;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# CONEXÃO COM SUPABASE
# ==================================================

@st.cache_resource
def conectar_supabase():
    configuracao = st.secrets["supabase"]
    url = configuracao["url"]

    chave = configuracao.get("secret_key")
    if not chave:
        chave = configuracao["key"]

    return create_client(url, chave)


try:
    supabase = conectar_supabase()
except Exception as erro:
    st.error("Não foi possível conectar ao Supabase.")
    st.caption(str(erro))
    st.stop()


# ==================================================
# CONCESSIONÁRIA
# ==================================================

def obter_concessionaria():
    resultado = (
        supabase.table("concessionarias")
        .select("*")
        .limit(1)
        .execute()
    )

    if resultado.data:
        return resultado.data[0]["id"]

    resultado = (
        supabase.table("concessionarias")
        .insert({"nome": "Minha Concessionária"})
        .execute()
    )

    return resultado.data[0]["id"]


try:
    concessionaria_id = obter_concessionaria()
except Exception as erro:
    st.error("Erro ao carregar a concessionária.")
    st.code(str(erro))
    st.stop()


# ==================================================
# FORMATAÇÃO BRASILEIRA
# ==================================================

def moeda(valor):
    valor = float(valor or 0)
    numero = f"{valor:,.2f}"
    numero = numero.replace(",", "X")
    numero = numero.replace(".", ",")
    numero = numero.replace("X", ".")
    return f"R$ {numero}"


def formatar_km(valor):
    valor = int(valor or 0)
    return f"{valor:,}".replace(",", ".") + " km"


def formatar_ano(valor):
    return str(int(valor or 0))


# ==================================================
# VEÍCULOS
# ==================================================

def buscar_veiculos():
    resultado = (
        supabase.table("veiculos")
        .select("*")
        .eq("concessionaria_id", concessionaria_id)
        .order("criado_em", desc=True)
        .execute()
    )

    return resultado.data or []


def atualizar_veiculo(veiculo_id, dados):
    return (
        supabase.table("veiculos")
        .update(dados)
        .eq("id", veiculo_id)
        .eq("concessionaria_id", concessionaria_id)
        .execute()
    )


def excluir_veiculo(veiculo_id):
    return (
        supabase.table("veiculos")
        .delete()
        .eq("id", veiculo_id)
        .eq("concessionaria_id", concessionaria_id)
        .execute()
    )


# ==================================================
# FOTOS
# ==================================================

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

    caminho = f"{concessionaria_id}/{uuid.uuid4().hex}.{extensao}"

    supabase.storage.from_("fotos-veiculos").upload(
        caminho,
        arquivo.getvalue(),
        {
            "content-type": tipos[extensao],
            "upsert": "false",
        },
    )

    return caminho


def obter_url_foto(caminho):
    if not caminho:
        return None

    try:
        resultado = (
            supabase.storage
            .from_("fotos-veiculos")
            .create_signed_url(caminho, 3600)
        )

        return resultado.get("signedURL") or resultado.get("signedUrl")

    except Exception:
        return None


# ==================================================
# MENU
# ==================================================

with st.sidebar:
    st.markdown("# 🚘 AUTO PRO")
    st.caption("GESTÃO AUTOMOTIVA")
    st.divider()

    pagina = st.radio(
        "MENU PRINCIPAL",
        [
            "Dashboard",
            "Estoque de veículos",
            "Cadastrar veículo",
            "Editar veículo",
        ],
    )

    st.divider()
    st.caption("Sistema Automotivo Pro")
    st.caption("Versão de desenvolvimento")


# ==================================================
# CARREGAMENTO DOS DADOS
# ==================================================

try:
    veiculos = buscar_veiculos()
except Exception as erro:
    st.error("Não foi possível carregar o estoque.")
    st.code(str(erro))
    st.stop()


# ==================================================
# DASHBOARD
# ==================================================

if pagina == "Dashboard":
    st.title("Dashboard")
    st.caption("Visão geral da sua concessionária")

    total = len(veiculos)

    disponiveis = sum(
        1 for v in veiculos
        if v.get("status") == "Disponível"
    )

    reservados = sum(
        1 for v in veiculos
        if v.get("status") == "Reservado"
    )

    vendidos = sum(
        1 for v in veiculos
        if v.get("status") == "Vendido"
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

    st.metric(
        "VALOR DO ESTOQUE NÃO VENDIDO",
        moeda(valor_estoque),
    )

    st.divider()
    st.subheader("Veículos recentes")

    if not veiculos:
        st.info(
            "Seu estoque está vazio. "
            "Cadastre seu primeiro veículo."
        )
    else:
        for v in veiculos[:5]:
            st.markdown(
                f"**{v.get('marca', '')} {v.get('modelo', '')}** "
                f"— {formatar_ano(v.get('ano'))} "
                f"— {moeda(v.get('preco'))}"
            )
            st.caption(
                f"{formatar_km(v.get('quilometragem'))} "
                f"• {v.get('status', 'Disponível')}"
            )


# ==================================================
# ESTOQUE DE VEÍCULOS
# ==================================================

elif pagina == "Estoque de veículos":
    st.title("Estoque de veículos")
    st.caption("Consulte e gerencie os veículos cadastrados.")

    col_busca, col_filtro = st.columns([2, 1])

    with col_busca:
        busca = st.text_input(
            "Buscar veículo",
            placeholder="Digite a marca ou o modelo...",
        )

    with col_filtro:
        filtro = st.selectbox(
            "Filtrar por status",
            ["Todos", "Disponível", "Reservado", "Vendido"],
        )

    filtrados = veiculos

    if busca:
        filtrados = [
            v for v in filtrados
            if busca.casefold() in v.get("marca", "").casefold()
            or busca.casefold() in v.get("modelo", "").casefold()
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
                col_foto, col_info, col_acoes = st.columns([1, 2, 1])

                with col_foto:
                    foto = obter_url_foto(v.get("foto_url"))

                    if foto:
                        st.image(foto, use_container_width=True)
                    else:
                        st.markdown("📷 Foto não cadastrada")

                with col_info:
                    st.subheader(
                        f"{v.get('marca', '')} {v.get('modelo', '')}"
                    )
                    st.write(f"Ano: {formatar_ano(v.get('ano'))}")
                    st.write(
                        f"Quilometragem: "
                        f"{formatar_km(v.get('quilometragem'))}"
                    )
                    st.markdown(f"### {moeda(v.get('preco'))}")
                    st.caption(f"Status: {v.get('status', 'Disponível')}")

                with col_acoes:
                    status_atual = v.get("status", "Disponível")

                    opcoes_status = [
                        "Disponível",
                        "Reservado",
                        "Vendido",
                    ]

                    indice = (
                        opcoes_status.index(status_atual)
                        if status_atual in opcoes_status
                        else 0
                    )

                    novo_status = st.selectbox(
                        "Status",
                        opcoes_status,
                        index=indice,
                        key=f"status_{v['id']}",
                    )

                    if st.button(
                        "Salvar status",
                        key=f"salvar_status_{v['id']}",
                        use_container_width=True,
                    ):
                        try:
                            atualizar_veiculo(
                                v["id"],
                                {"status": novo_status},
                            )
                            st.success("Status atualizado!")
                            st.rerun()
                        except Exception as erro:
                            st.error("Não foi possível atualizar o status.")
                            st.caption(str(erro))

                    chave_confirmacao = f"confirmar_exclusao_{v['id']}"

                    if st.button(
                        "Excluir veículo",
                        key=f"excluir_{v['id']}",
                        use_container_width=True,
                    ):
                        st.session_state[chave_confirmacao] = True

                    if st.session_state.get(chave_confirmacao):
                        st.warning("Confirma a exclusão deste veículo?")
                        sim, nao = st.columns(2)

                        if sim.button("Sim", key=f"sim_{v['id']}"):
                            try:
                                excluir_veiculo(v["id"])
                                st.session_state.pop(chave_confirmacao, None)
                                st.success("Veículo excluído.")
                                st.rerun()
                            except Exception as erro:
                                st.error("Não foi possível excluir.")
                                st.caption(str(erro))

                        if nao.button("Cancelar", key=f"nao_{v['id']}"):
                            st.session_state.pop(chave_confirmacao, None)
                            st.rerun()


# ==================================================
# CADASTRAR VEÍCULO
# ==================================================

elif pagina == "Cadastrar veículo":
    st.title("Cadastrar veículo")
    st.caption("Adicione um veículo ao estoque.")

    with st.form("form_cadastrar", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca", placeholder="Ex.: Toyota")
            modelo = st.text_input("Modelo", placeholder="Ex.: Corolla")

            ano = st.number_input(
                "Ano",
                min_value=1900,
                max_value=2100,
                value=2020,
                step=1,
            )

        with col2:
            km = st.number_input(
                "Quilometragem (km)",
                min_value=0,
                value=0,
                step=1000,
            )

            preco = st.number_input(
                "Preço (R$)",
                min_value=0.0,
                value=0.0,
                step=500.0,
                format="%.2f",
            )

            status = st.selectbox(
                "Status",
                ["Disponível", "Reservado", "Vendido"],
            )

        foto = st.file_uploader(
            "Foto do veículo (opcional, até 5 MB)",
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

                supabase.table("veiculos").insert(dados).execute()

                st.success("Veículo cadastrado com sucesso!")
                st.rerun()

            except Exception as erro:
                st.error("Não foi possível cadastrar o veículo.")
                st.caption(str(erro))


# ==================================================
# EDITAR VEÍCULO
# ==================================================

elif pagina == "Editar veículo":
    st.title("Editar veículo")
    st.caption("Atualize os dados de um veículo já cadastrado.")

    if not veiculos:
        st.info("Não existem veículos cadastrados para editar.")
    else:
        opcoes = {
            (
                f"{v.get('marca', '')} {v.get('modelo', '')} "
                f"— {v.get('ano', '')} "
                f"— {moeda(v.get('preco'))}"
            ): v
            for v in veiculos
        }

        selecionado = st.selectbox(
            "Selecione o veículo",
            list(opcoes.keys()),
        )

        v = opcoes[selecionado]

        with st.form("form_editar"):
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
                    step=1,
                )

            with col2:
                km = st.number_input(
                    "Quilometragem (km)",
                    min_value=0,
                    value=int(v.get("quilometragem") or 0),
                    step=1000,
                )

                preco = st.number_input(
                    "Preço (R$)",
                    min_value=0.0,
                    value=float(v.get("preco") or 0),
                    step=500.0,
                    format="%.2f",
                )

                status_opcoes = [
                    "Disponível",
                    "Reservado",
                    "Vendido",
                ]

                status_atual = v.get("status", "Disponível")

                status = st.selectbox(
                    "Status",
                    status_opcoes,
                    index=(
                        status_opcoes.index(status_atual)
                        if status_atual in status_opcoes
                        else 0
                    ),
                )

            foto_atual = obter_url_foto(v.get("foto_url"))

            if foto_atual:
                st.image(
                    foto_atual,
                    caption="Foto atual",
                    width=300,
                )

            nova_foto = st.file_uploader(
                "Substituir foto (opcional, até 5 MB)",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"nova_foto_{v['id']}",
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
                        dados["foto_url"] = salvar_foto(nova_foto)

                    atualizar_veiculo(v["id"], dados)

                    st.success("Alterações salvas com sucesso!")
                    st.rerun()

                except Exception as erro:
                    st.error("Não foi possível salvar as alterações.")
                    st.caption(str(erro))


# ==================================================
# RODAPÉ
# ==================================================

st.divider()
st.caption("AUTO PRO • Sistema de Gestão Automotiva")
