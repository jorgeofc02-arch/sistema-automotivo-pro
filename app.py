
import uuid
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st
from supabase import create_client

# =====================================================
# CONFIGURAÇÃO E VISUAL
# =====================================================
st.set_page_config(page_title="Sistema Automotivo Pro", page_icon="🚘", layout="wide")
st.markdown("""
<style>
.stApp { background-color: #0b1120; color: #e5e7eb; }
[data-testid="stSidebar"] { background-color: #111827; }
[data-testid="stMetric"] { background: #111827; border: 1px solid #263244; padding: 15px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)
st.title("🚘 Sistema Automotivo Pro")
st.caption("Gestão profissional de veículos")

STATUS_VEICULOS = ["Disponível", "Reservado", "Vendido"]

# =====================================================
# SUPABASE
# =====================================================
@st.cache_resource
def conectar_supabase():
    config = st.secrets["supabase"]
    url = config.get("url")
    chave = config.get("secret_key") or config.get("key")
    if not url or not chave:
        raise RuntimeError("Configure url e key nos Secrets do Streamlit.")
    return create_client(url, chave)

try:
    supabase = conectar_supabase()
except Exception as erro:
    st.error("Erro ao conectar ao Supabase. Confira os Secrets do Streamlit.")
    st.code(str(erro))
    st.stop()

# =====================================================
# FORMATAÇÃO E CONVERSÃO DE PREÇOS
# =====================================================
def moeda(valor):
    try:
        numero = Decimal(str(valor if valor is not None else 0))
    except (InvalidOperation, ValueError, TypeError):
        numero = Decimal("0")
    texto = f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def interpretar_preco(entrada):
    """Aceita 1000000, 1.000.000,00, R$ 1.000.000,00 e 1.000.000.00."""
    texto = str(entrada or "").strip().replace("R$", "").replace(" ", "")
    texto = re.sub(r"[^0-9,.\-]", "", texto)
    if not texto or texto in (",", ".", "-", "-,", "-."):
        raise ValueError("Digite um preço válido. Exemplo: 1.000.000,00.")
    if texto.startswith("-"):
        raise ValueError("O preço não pode ser negativo.")

    # Formato brasileiro padrão: 1.000.000,00
    if "," in texto:
        if texto.count(",") != 1:
            raise ValueError("Preço inválido. Exemplo: 1.000.000,00.")
        parte_inteira, parte_decimal = texto.split(",")
        parte_inteira = parte_inteira.replace(".", "")
        if parte_decimal and not parte_decimal.isdigit():
            raise ValueError("Preço inválido. Exemplo: 1.000.000,00.")
        normalizado = parte_inteira + ("." + parte_decimal if parte_decimal else "")
    elif texto.count(".") > 1:
        # Também corrige a entrada que causou o erro: 1.000.000.00
        partes = texto.split(".")
        if len(partes[-1]) in (1, 2) and all(p.isdigit() for p in partes):
            normalizado = "".join(partes[:-1]) + "." + partes[-1]
        else:
            normalizado = "".join(partes)
    elif "." in texto:
        inteira, decimal = texto.split(".")
        # 1.000 normalmente significa mil; 1000.50 significa mil e cinquenta centavos.
        if len(decimal) == 3 and inteira.isdigit() and decimal.isdigit():
            normalizado = inteira + decimal
        else:
            normalizado = texto
    else:
        normalizado = texto

    try:
        valor = Decimal(normalizado)
    except InvalidOperation:
        raise ValueError("Preço inválido. Exemplo: 1.000.000,00.")
    if not valor.is_finite() or valor < 0:
        raise ValueError("O preço não pode ser negativo.")
    return float(valor.quantize(Decimal("0.01")))


def campo_preco(rotulo, valor=0, chave="preco"):
    try:
        inicial = f"{Decimal(str(valor or 0)):.2f}".replace(".", ",")
    except (InvalidOperation, ValueError, TypeError):
        inicial = "0,00"
    return st.text_input(rotulo, value=inicial, key=chave,
                         placeholder="Ex.: 1.000.000,00",
                         help="Digite 1000000 ou 1.000.000,00. O sistema interpreta o valor em reais.")


def formatar_km(valor):
    try:
        km = int(float(valor or 0))
    except (ValueError, TypeError):
        km = 0
    return f"{km:,}".replace(",", ".") + " km"

# =====================================================
# CONCESSIONÁRIA E BANCO DE DADOS
# =====================================================
def obter_concessionaria_id():
    resposta = supabase.table("concessionarias").select("id").limit(1).execute()
    if resposta.data:
        return resposta.data[0]["id"]
    resposta = supabase.table("concessionarias").insert({"nome": "Minha Concessionária"}).execute()
    if resposta.data:
        return resposta.data[0]["id"]
    raise RuntimeError("Não foi possível criar a concessionária.")

try:
    concessionaria_id = obter_concessionaria_id()
except Exception as erro:
    st.error("Erro ao acessar a tabela concessionarias.")
    st.code(str(erro))
    st.stop()


def buscar_veiculos():
    resposta = (supabase.table("veiculos").select("*")
                .eq("concessionaria_id", concessionaria_id)
                .order("criado_em", desc=True).execute())
    return resposta.data or []


def atualizar_veiculo(veiculo_id, dados):
    return (supabase.table("veiculos").update(dados)
            .eq("id", veiculo_id).eq("concessionaria_id", concessionaria_id).execute())


def excluir_veiculo(veiculo_id):
    return (supabase.table("veiculos").delete()
            .eq("id", veiculo_id).eq("concessionaria_id", concessionaria_id).execute())

# =====================================================
# FOTOS NO STORAGE
# =====================================================
def salvar_foto(arquivo):
    if arquivo is None:
        return None
    conteudo = arquivo.getvalue()
    if len(conteudo) > 5 * 1024 * 1024:
        raise ValueError("A foto deve ter no máximo 5 MB.")
    nome = arquivo.name or "foto.jpg"
    extensao = nome.rsplit(".", 1)[-1].lower() if "." in nome else "jpg"
    if extensao not in ["jpg", "jpeg", "png", "webp"]:
        extensao = "jpg"
    caminho = f"{concessionaria_id}/{uuid.uuid4().hex}.{extensao}"
    supabase.storage.from_("fotos-veiculos").upload(
        path=caminho, file=conteudo,
        file_options={"content-type": arquivo.type or "image/jpeg", "upsert": "false"})
    return caminho


def obter_url_foto(caminho):
    if not caminho:
        return None
    try:
        resultado = supabase.storage.from_("fotos-veiculos").create_signed_url(caminho, 3600)
        return resultado.get("signedURL") or resultado.get("signedUrl")
    except Exception:
        return None


def mostrar_foto(caminho, largura=220):
    url = obter_url_foto(caminho)
    if url:
        st.image(url, width=largura)
    else:
        st.caption("Sem foto disponível.")

# =====================================================
# MENU
# =====================================================
with st.sidebar:
    st.markdown("## 🚘 Menu")
    pagina = st.radio("Navegação", ["Dashboard", "Estoque de veículos", "Cadastrar veículo", "Editar veículo"], label_visibility="collapsed")
    st.divider()
    st.caption("Sistema Automotivo Pro")

# =====================================================
# DASHBOARD
# =====================================================
if pagina == "Dashboard":
    st.subheader("Dashboard")
    try:
        veiculos = buscar_veiculos()
        total = len(veiculos)
        disponiveis = sum(v.get("status") == "Disponível" for v in veiculos)
        reservados = sum(v.get("status") == "Reservado" for v in veiculos)
        vendidos = sum(v.get("status") == "Vendido" for v in veiculos)
        valor_estoque = sum(float(v.get("preco") or 0) for v in veiculos if v.get("status") != "Vendido")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de veículos", total)
        c2.metric("Disponíveis", disponiveis)
        c3.metric("Reservados", reservados)
        c4.metric("Vendidos", vendidos)
        st.markdown("### Valor do estoque não vendido")
        st.markdown(f"## {moeda(valor_estoque)}")
        st.divider()
        st.markdown("### Veículos recentes")
        if veiculos:
            tabela = [{"Marca": v.get("marca", ""), "Modelo": v.get("modelo", ""),
                       "Ano": v.get("ano", ""), "Quilometragem": formatar_km(v.get("quilometragem")),
                       "Preço": moeda(v.get("preco")), "Status": v.get("status", "")}
                      for v in veiculos[:5]]
            st.dataframe(pd.DataFrame(tabela), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum veículo cadastrado ainda.")
    except Exception as erro:
        st.error("Não foi possível carregar o dashboard.")
        st.code(str(erro))

# =====================================================
# ESTOQUE
# =====================================================
elif pagina == "Estoque de veículos":
    st.subheader("Estoque de veículos")
    try:
        veiculos = buscar_veiculos()
        if not veiculos:
            st.info("Nenhum veículo cadastrado.")
        else:
            col_busca, col_status = st.columns([2, 1])
            busca = col_busca.text_input("Buscar por marca ou modelo", placeholder="Ex.: Toyota Corolla")
            filtro_status = col_status.selectbox("Filtrar por status", ["Todos"] + STATUS_VEICULOS)
            filtrados = veiculos
            if busca.strip():
                termo = busca.strip().lower()
                filtrados = [v for v in filtrados if termo in str(v.get("marca", "")).lower() or termo in str(v.get("modelo", "")).lower()]
            if filtro_status != "Todos":
                filtrados = [v for v in filtrados if v.get("status") == filtro_status]
            st.caption(f"{len(filtrados)} veículo(s) encontrado(s)")
            for veiculo in filtrados:
                with st.container(border=True):
                    foto_col, dados_col, acoes_col = st.columns([1, 2, 1])
                    with foto_col:
                        mostrar_foto(veiculo.get("foto_url"))
                    with dados_col:
                        st.markdown(f"### {veiculo.get('marca', '')} {veiculo.get('modelo', '')}")
                        st.write(f"**Ano:** {veiculo.get('ano', '—')}")
                        st.write(f"**Quilometragem:** {formatar_km(veiculo.get('quilometragem'))}")
                        st.markdown(f"**Preço:** {moeda(veiculo.get('preco'))}")
                        st.write(f"**Status:** {veiculo.get('status', 'Disponível')}")
                    with acoes_col:
                        status_atual = veiculo.get("status")
                        indice = STATUS_VEICULOS.index(status_atual) if status_atual in STATUS_VEICULOS else 0
                        novo_status = st.selectbox("Alterar status", STATUS_VEICULOS, index=indice, key=f"status_{veiculo['id']}")
                        if st.button("Salvar status", key=f"salvar_status_{veiculo['id']}", use_container_width=True):
                            try:
                                atualizar_veiculo(veiculo["id"], {"status": novo_status})
                                st.success("Status atualizado!")
                                st.rerun()
                            except Exception as erro:
                                st.error("Não foi possível atualizar o status.")
                                st.code(str(erro))
                        confirmar = st.checkbox("Confirmar exclusão", key=f"confirmar_{veiculo['id']}")
                        if st.button("Excluir veículo", key=f"excluir_{veiculo['id']}", disabled=not confirmar, use_container_width=True):
                            try:
                                excluir_veiculo(veiculo["id"])
                                st.success("Veículo excluído.")
                                st.rerun()
                            except Exception as erro:
                                st.error("Não foi possível excluir o veículo.")
                                st.code(str(erro))
    except Exception as erro:
        st.error("Não foi possível carregar o estoque.")
        st.code(str(erro))

# =====================================================
# CADASTRAR VEÍCULO
# =====================================================
elif pagina == "Cadastrar veículo":
    st.subheader("Cadastrar veículo")
    with st.form("form_cadastrar_veiculo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        marca = c1.text_input("Marca *", placeholder="Ex.: Toyota")
        modelo = c2.text_input("Modelo *", placeholder="Ex.: Corolla XEi")
        c3, c4 = st.columns(2)
        ano = c3.number_input("Ano *", min_value=1900, max_value=2100, value=2020, step=1)
        quilometragem = c4.number_input("Quilometragem (km) *", min_value=0, value=0, step=1000)
        preco_texto = campo_preco("Preço (R$) *", 0, "preco_cadastro")
        status = st.selectbox("Status", STATUS_VEICULOS)
        foto = st.file_uploader("Foto do veículo (opcional)", type=["jpg", "jpeg", "png", "webp"])
        enviar = st.form_submit_button("Cadastrar veículo", use_container_width=True)
    if enviar:
        if not marca.strip() or not modelo.strip():
            st.error("Preencha a marca e o modelo.")
        else:
            try:
                preco = interpretar_preco(preco_texto)
                if preco <= 0:
                    raise ValueError("Informe um preço maior que zero.")
                with st.spinner("Salvando veículo..."):
                    caminho_foto = salvar_foto(foto) if foto is not None else None
                    dados = {"concessionaria_id": concessionaria_id, "marca": marca.strip(), "modelo": modelo.strip(),
                             "ano": int(ano), "quilometragem": int(quilometragem), "preco": preco,
                             "status": status, "foto_url": caminho_foto}
                    supabase.table("veiculos").insert(dados).execute()
                st.success("Veículo cadastrado com sucesso!")
                st.rerun()
            except ValueError as erro:
                st.error(str(erro))
            except Exception as erro:
                st.error("Não foi possível cadastrar o veículo.")
                st.code(str(erro))

# =====================================================
# EDITAR VEÍCULO
# =====================================================
elif pagina == "Editar veículo":
    st.subheader("Editar veículo")
    try:
        veiculos = buscar_veiculos()
    except Exception as erro:
        st.error("Não foi possível carregar os veículos.")
        st.code(str(erro))
        veiculos = []
    if not veiculos:
        st.info("Não há veículos para editar.")
    else:
        opcoes = {f"{v.get('marca', '')} {v.get('modelo', '')} — {v.get('ano', '')} ({moeda(v.get('preco'))})": v for v in veiculos}
        escolhido_label = st.selectbox("Escolha o veículo", list(opcoes.keys()))
        escolhido = opcoes[escolhido_label]
        with st.form("form_editar_veiculo"):
            c1, c2 = st.columns(2)
            marca_ed = c1.text_input("Marca *", value=str(escolhido.get("marca") or ""))
            modelo_ed = c2.text_input("Modelo *", value=str(escolhido.get("modelo") or ""))
            c3, c4 = st.columns(2)
            ano_ed = c3.number_input("Ano *", min_value=1900, max_value=2100,
                                     value=max(1900, min(2100, int(escolhido.get("ano") or 2020))), step=1)
            km_ed = c4.number_input("Quilometragem (km) *", min_value=0,
                                    value=max(0, int(escolhido.get("quilometragem") or 0)), step=1000)
            preco_ed_texto = campo_preco("Preço (R$) *", escolhido.get("preco") or 0, f"preco_ed_{escolhido['id']}")
            status_atual = escolhido.get("status")
            indice_status = STATUS_VEICULOS.index(status_atual) if status_atual in STATUS_VEICULOS else 0
            status_ed = st.selectbox("Status", STATUS_VEICULOS, index=indice_status)
            foto_nova = st.file_uploader("Substituir foto (opcional)", type=["jpg", "jpeg", "png", "webp"])
            salvar_edicao = st.form_submit_button("Salvar alterações", use_container_width=True)
        if salvar_edicao:
            if not marca_ed.strip() or not modelo_ed.strip():
                st.error("Preencha a marca e o modelo.")
            else:
                try:
                    preco_ed = interpretar_preco(preco_ed_texto)
                    if preco_ed <= 0:
                        raise ValueError("Informe um preço maior que zero.")
                    caminho_foto_ed = escolhido.get("foto_url")
                    if foto_nova is not None:
                        caminho_foto_ed = salvar_foto(foto_nova)
                    dados_ed = {"marca": marca_ed.strip(), "modelo": modelo_ed.strip(), "ano": int(ano_ed),
                                "quilometragem": int(km_ed), "preco": preco_ed, "status": status_ed,
                                "foto_url": caminho_foto_ed}
                    atualizar_veiculo(escolhido["id"], dados_ed)
                    st.success("Veículo atualizado com sucesso!")
                    st.rerun()
                except ValueError as erro:
                    st.error(str(erro))
                except Exception as erro:
                    st.error("Não foi possível salvar as alterações.")
                    st.code(str(erro))

st.divider()
st.caption("Sistema Automotivo Pro • Gestão de veículos")
