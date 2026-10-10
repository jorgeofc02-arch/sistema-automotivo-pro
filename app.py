import streamlit as st
import uuid
import re
from decimal import Decimal, InvalidOperation
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
.stApp { background: #0b0f19; color: #f1f5f9; }
[data-testid="stSidebar"] { background: #111827; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }
h1, h2, h3 { color: #f8fafc; }
[data-testid="stMetric"] {
    background: #151d2e;
    border: 1px solid #263248;
    border-radius: 12px;
    padding: 18px;
}
div.stButton > button, div.stFormSubmitButton > button {
    border-radius: 8px;
    min-height: 42px;
}
</style>

""", unsafe_allow_html=True)

# ==================================================

# SUPABASE

# ==================================================

@st.cache_resource
def conectar_supabase():
config = st.secrets["supabase"]
chave = config.get("secret_key") or config["key"]
return create_client(config["url"], chave)

try:
supabase = conectar_supabase()
except Exception as erro:
st.error("Não foi possível conectar ao Supabase.")
st.caption(str(erro))
st.stop()

def obter_concessionaria():
resposta = (
supabase.table("concessionarias")
.select("*")
.limit(1)
.execute()
)

```
if resposta.data:
    return resposta.data[0]["id"]

resposta = (
    supabase.table("concessionarias")
    .insert({"nome": "Minha Concessionária"})
    .execute()
)
return resposta.data[0]["id"]
```

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
numero = Decimal(str(valor or 0))
texto = f"{numero:,.2f}"
texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
return f"R$ {texto}"

def formatar_km(valor):
return f"{int(valor or 0):,}".replace(",", ".") + " km"

def interpretar_preco(texto):
"""
Aceita, por exemplo:
45000
45000,50
45.000,50
R$ 45.000,50
45000.50
"""
texto = str(texto or "").strip()
texto = texto.replace("R$", "").replace(" ", "")
texto = re.sub(r"[^0-9,.-]", "", texto)

```
if not texto or texto in (",", ".", "-", "-,", "-."):
    raise ValueError("Digite um preço válido.")

if "," in texto:
    # A vírgula é o separador decimal brasileiro.
    texto = texto.replace(".", "")
    texto = texto.replace(",", ".")
elif texto.count(".") > 1:
    # Vários pontos indicam separadores de milhares.
    texto = texto.replace(".", "")
elif "." in texto:
    # Um único ponto seguido de três dígitos é tratado
    # como separador de milhares; nos demais casos, decimal.
    partes = texto.split(".")
    if len(partes[-1]) == 3 and len(partes[0]) >= 1:
        texto = "".join(partes)

try:
    valor = Decimal(texto)
except InvalidOperation:
    raise ValueError("Preço inválido. Exemplo: 45.000,00.")

if not valor.is_finite() or valor < 0:
    raise ValueError("O preço não pode ser negativo.")

return float(valor)
```

def campo_preco(rotulo, valor_inicial, chave):
valor_formatado = f"{Decimal(str(valor_inicial or 0)):.2f}"
return st.text_input(
rotulo,
value=valor_formatado,
key=chave,
help="Exemplos aceitos: 45000, 45.000,00 ou R$ 45.000,00.",
placeholder="Ex.: 45.000,00",
)

# ==================================================

# BANCO DE DADOS

# ==================================================

def buscar_veiculos():
resposta = (
supabase.table("veiculos")
.select("*")
.eq("concessionaria_id", concessionaria_id)
.order("criado_em", desc=True)
.execute()
)
return resposta.data or []

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

```
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
    raise ValueError("Use uma imagem JPG, PNG ou WEBP.")

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
```

def obter_url_foto(caminho):
if not caminho:
return None

```
try:
    resposta = (
        supabase.storage
        .from_("fotos-veiculos")
        .create_signed_url(caminho, 3600)
    )
    return resposta.get("signedURL") or resposta.get("signedUrl")
except Exception:
    return None
```

# ==================================================

# MENU

# ==================================================

with st.sidebar:
st.markdown("# 🚘 AUTO PRO")
st.caption("GESTÃO AUTOMOTIVA")
st.divider()

```
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
```

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

```
disponiveis = sum(v.get("status") == "Disponível" for v in veiculos)
reservados = sum(v.get("status") == "Reservado" for v in veiculos)
vendidos = sum(v.get("status") == "Vendido" for v in veiculos)

valor_estoque = sum(
    Decimal(str(v.get("preco") or 0))
    for v in veiculos
    if v.get("status") != "Vendido"
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("TOTAL DE VEÍCULOS", len(veiculos))
c2.metric("DISPONÍVEIS", disponiveis)
c3.metric("RESERVADOS", reservados)
c4.metric("VENDIDOS", vendidos)

st.metric("VALOR DO ESTOQUE NÃO VENDIDO", moeda(valor_estoque))
st.divider()
st.subheader("Veículos recentes")

if not veiculos:
    st.info("Seu estoque está vazio. Cadastre seu primeiro veículo.")
else:
    for v in veiculos[:5]:
        st.markdown(
            f"**{v.get('marca', '')} {v.get('modelo', '')}** "
            f"— {v.get('ano', '')} — {moeda(v.get('preco'))}"
        )
        st.caption(
            f"{formatar_km(v.get('quilometragem'))} "
            f"• {v.get('status', 'Disponível')}"
        )
```

# ==================================================

# ESTOQUE

# ==================================================

elif pagina == "Estoque de veículos":
st.title("Estoque de veículos")
busca_col, filtro_col = st.columns([2, 1])

```
with busca_col:
    busca = st.text_input("Buscar veículo", placeholder="Marca ou modelo...")

with filtro_col:
    filtro = st.selectbox(
        "Filtrar por status",
        ["Todos", "Disponível", "Reservado", "Vendido"],
    )

filtrados = [
    v for v in veiculos
    if (
        not busca
        or busca.casefold() in v.get("marca", "").casefold()
        or busca.casefold() in v.get("modelo", "").casefold()
    )
    and (filtro == "Todos" or v.get("status") == filtro)
]

st.caption(f"{len(filtrados)} veículo(s) encontrado(s)")

if not filtrados:
    st.info("Nenhum veículo encontrado.")
else:
    for v in filtrados:
        with st.container(border=True):
            foto_col, info_col, acao_col = st.columns([1, 2, 1])

            with foto_col:
                foto = obter_url_foto(v.get("foto_url"))
                if foto:
                    st.image(foto, use_container_width=True)
                else:
                    st.caption("📷 Foto não cadastrada")

            with info_col:
                st.subheader(f"{v.get('marca', '')} {v.get('modelo', '')}")
                st.write(f"Ano: {v.get('ano', '-')}")
                st.write(f"Quilometragem: {formatar_km(v.get('quilometragem'))}")
                st.markdown(f"### {moeda(v.get('preco'))}")
                st.caption(f"Status: {v.get('status', 'Disponível')}")

            with acao_col:
                estados = ["Disponível", "Reservado", "Vendido"]
                status_atual = v.get("status", "Disponível")
                indice = estados.index(status_atual) if status_atual in estados else 0

                novo_status = st.selectbox(
                    "Status",
                    estados,
                    index=indice,
                    key=f"status_{v['id']}",
                )

                if st.button("Salvar status", key=f"salvar_{v['id']}"):
                    try:
                        atualizar_veiculo(v["id"], {"status": novo_status})
                        st.success("Status atualizado.")
                        st.rerun()
                    except Exception as erro:
                        st.error("Erro ao atualizar status.")
                        st.caption(str(erro))

                confirm_key = f"confirmar_exclusao_{v['id']}"

                if st.button("Excluir veículo", key=f"excluir_{v['id']}"):
                    st.session_state[confirm_key] = True

                if st.session_state.get(confirm_key):
                    st.warning("Confirma a exclusão deste veículo?")
                    sim, nao = st.columns(2)

                    if sim.button("Sim, excluir", key=f"sim_{v['id']}"):
                        try:
                            excluir_veiculo(v["id"])
                            st.session_state.pop(confirm_key, None)
                            st.success("Veículo excluído.")
                            st.rerun()
                        except Exception as erro:
                            st.error("Erro ao excluir veículo.")
                            st.caption(str(erro))

                    if nao.button("Cancelar", key=f"nao_{v['id']}"):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
```

# ==================================================

# CADASTRO

# ==================================================

elif pagina == "Cadastrar veículo":
st.title("Cadastrar veículo")

```
with st.form("form_cadastrar", clear_on_submit=True):
    c1, c2 = st.columns(2)

    with c1:
        marca = st.text_input("Marca", placeholder="Ex.: Toyota")
        modelo = st.text_input("Modelo", placeholder="Ex.: Corolla")
        ano = st.number_input("Ano", min_value=1900, max_value=2100, value=2020, step=1)

    with c2:
        km = st.number_input("Quilometragem (km)", min_value=0, value=0, step=1000)
        preco_texto = campo_preco("Preço (R$)", 0, "preco_cadastro")
        status = st.selectbox("Status", ["Disponível", "Reservado", "Vendido"])

    foto = st.file_uploader(
        "Foto do veículo (opcional, máximo 5 MB)",
        type=["jpg", "jpeg", "png", "webp"],
    )

    cadastrar = st.form_submit_button("Cadastrar veículo", use_container_width=True)

if cadastrar:
    if not marca.strip() or not modelo.strip():
        st.error("Preencha a marca e o modelo.")
    else:
        try:
            preco = interpretar_preco(preco_texto)
            caminho = salvar_foto(foto) if foto else None

            dados = {
                "concessionaria_id": concessionaria_id,
                "marca": marca.strip(),
                "modelo": modelo.strip(),
                "ano": int(ano),
                "quilometragem": int(km),
                "preco": preco,
                "status": status,
                "foto_url": caminho,
            }

            supabase.table("veiculos").insert(dados).execute()
            st.success(f"Veículo cadastrado por {moeda(preco)}.")
            st.rerun()

        except Exception as erro:
            st.error("Não foi possível cadastrar o veículo.")
            st.caption(str(erro))
```

# ==================================================

# EDIÇÃO

# ==================================================

elif pagina == "Editar veículo":
st.title("Editar veículo")

```
if not veiculos:
    st.info("Cadastre um veículo antes de tentar editá-lo.")
else:
    opcoes = {
        f"{v.get('marca', '')} {v.get('modelo', '')} — {v.get('ano', '')} — {moeda(v.get('preco'))}": v
        for v in veiculos
    }

    selecionado = st.selectbox("Selecione o veículo", list(opcoes.keys()))
    v = opcoes[selecionado]

    with st.form("form_editar"):
        c1, c2 = st.columns(2)

        with c1:
            marca = st.text_input("Marca", value=v.get("marca", ""))
            modelo = st.text_input("Modelo", value=v.get("modelo", ""))
            ano = st.number_input(
                "Ano",
                min_value=1900,
                max_value=2100,
                value=int(v.get("ano") or 2020),
                step=1,
            )

        with c2:
            km = st.number_input(
                "Quilometragem (km)",
                min_value=0,
                value=int(v.get("quilometragem") or 0),
                step=1000,
            )
            preco_texto = campo_preco(
                "Preço (R$)",
                v.get("preco") or 0,
                f"preco_edicao_{v['id']}",
            )

            estados = ["Disponível", "Reservado", "Vendido"]
            atual = v.get("status", "Disponível")
            status = st.selectbox(
                "Status",
                estados,
                index=estados.index(atual) if atual in estados else 0,
            )

        foto_atual = obter_url_foto(v.get("foto_url"))
        if foto_atual:
            st.image(foto_atual, caption="Foto atual", width=300)

        nova_foto = st.file_uploader(
            "Substituir foto (opcional, máximo 5 MB)",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"foto_edicao_{v['id']}",
        )

        salvar = st.form_submit_button("Salvar alterações", use_container_width=True)

    if salvar:
        if not marca.strip() or not modelo.strip():
            st.error("Preencha a marca e o modelo.")
        else:
            try:
                preco = interpretar_preco(preco_texto)

                dados = {
                    "marca": marca.strip(),
                    "modelo": modelo.strip(),
                    "ano": int(ano),
                    "quilometragem": int(km),
                    "preco": preco,
                    "status": status,
                }

                if nova_foto:
                    dados["foto_url"] = salvar_foto(nova_foto)

                atualizar_veiculo(v["id"], dados)
                st.success(f"Alterações salvas. Preço: {moeda(preco)}.")
                st.rerun()

            except Exception as erro:
                st.error("Não foi possível salvar as alterações.")
                st.caption(str(erro))
```

# ==================================================

# RODAPÉ

# ==================================================

st.divider()
st.caption("AUTO PRO • Sistema de Gestão Automotiva")
