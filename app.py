import re
import uuid
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Sistema Automotivo Pro", page_icon="🚘", layout="wide")
st.markdown("""
<style>
.stApp { background-color: #0b1120; color: #e5e7eb; }
[data-testid="stSidebar"] { background-color: #111827; }
[data-testid="stMetric"] { background: #111827; border: 1px solid #263244; padding: 15px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)
st.title("🚘 Sistema Automotivo Pro")
st.caption("Gestão de estoque, vendas e faturamento")

STATUS_VEICULOS = ["Disponível", "Reservado", "Vendido"]

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
    if "," in texto:
        if texto.count(",") != 1:
            raise ValueError("Preço inválido. Exemplo: 1.000.000,00.")
        inteira, decimal = texto.split(",")
        inteira = inteira.replace(".", "")
        if decimal and not decimal.isdigit():
            raise ValueError("Preço inválido. Exemplo: 1.000.000,00.")
        normalizado = inteira + ("." + decimal if decimal else "")
    elif texto.count(".") > 1:
        partes = texto.split(".")
        if all(p.isdigit() for p in partes) and len(partes[-1]) in (1, 2):
            normalizado = "".join(partes[:-1]) + "." + partes[-1]
        else:
            normalizado = "".join(partes)
    elif "." in texto:
        inteira, decimal = texto.split(".")
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


def buscar_vendas(inicio=None, fim=None):
    consulta = (supabase.table("vendas").select("*")
                .eq("concessionaria_id", concessionaria_id))
    if inicio:
        consulta = consulta.gte("data_venda", inicio.isoformat())
    if fim:
        consulta = consulta.lte("data_venda", fim.isoformat())
    return (consulta.order("data_venda", desc=True).order("criado_em", desc=True).execute().data or [])


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


def custo_veiculo(veiculo):
    try:
        return float(veiculo.get("custo_compra") or 0)
    except (ValueError, TypeError):
        return 0.0

# Menu
with st.sidebar:
    st.markdown("## 🚘 Menu")
    pagina = st.radio("Navegação", ["Dashboard", "Estoque de veículos", "Cadastrar veículo", "Editar veículo", "Registrar venda", "Histórico de vendas", "Relatórios"], label_visibility="collapsed")
    st.divider()
    st.caption("Sistema Automotivo Pro")

# Dashboard
if pagina == "Dashboard":
    st.subheader("Dashboard")
    try:
        veiculos = buscar_veiculos()
        vendas = buscar_vendas()
        total = len(veiculos)
        disponiveis = sum(v.get("status") == "Disponível" for v in veiculos)
        reservados = sum(v.get("status") == "Reservado" for v in veiculos)
        vendidos = sum(v.get("status") == "Vendido" for v in veiculos)
        valor_estoque = sum(float(v.get("preco") or 0) for v in veiculos if v.get("status") != "Vendido")
        faturamento = sum(float(v.get("preco_venda") or 0) for v in vendas)
        lucro = sum(float(v.get("lucro_bruto") or 0) for v in vendas)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Veículos cadastrados", total)
        c2.metric("Disponíveis", disponiveis)
        c3.metric("Reservados", reservados)
        c4.metric("Vendidos", vendidos)
        c5, c6, c7 = st.columns(3)
        c5.metric("Valor do estoque", moeda(valor_estoque))
        c6.metric("Faturamento registrado", moeda(faturamento))
        c7.metric("Lucro bruto estimado", moeda(lucro), help="Vendas menos custo de compra informado; não inclui despesas, impostos ou taxas.")
        st.divider()
        st.markdown("### Veículos recentes")
        if veiculos:
            tabela = [{"Marca": v.get("marca", ""), "Modelo": v.get("modelo", ""), "Ano": v.get("ano", ""),
                       "Quilometragem": formatar_km(v.get("quilometragem")), "Preço anunciado": moeda(v.get("preco")),
                       "Custo de compra": moeda(v.get("custo_compra")), "Status": v.get("status", "")} for v in veiculos[:5]]
            st.dataframe(pd.DataFrame(tabela), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum veículo cadastrado ainda.")
        st.markdown("### Vendas recentes")
        if vendas:
            st.dataframe(pd.DataFrame([{"Data": v.get("data_venda"), "Veículo": f"{v.get('marca', '')} {v.get('modelo', '')}",
                                        "Preço de venda": moeda(v.get("preco_venda")), "Lucro bruto": moeda(v.get("lucro_bruto"))} for v in vendas[:5]]),
                         use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há vendas registradas.")
    except Exception as erro:
        st.error("Não foi possível carregar o dashboard. Confira se executou o SQL de configuração das vendas.")
        st.code(str(erro))

# Stock
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
                        st.markdown(f"**Preço anunciado:** {moeda(veiculo.get('preco'))}")
                        st.write(f"**Custo de compra:** {moeda(veiculo.get('custo_compra'))}")
                        st.write(f"**Status:** {veiculo.get('status', 'Disponível')}")
                    with acoes_col:
                        if veiculo.get("status") != "Vendido":
                            atual = veiculo.get("status")
                            indice = STATUS_VEICULOS.index(atual) if atual in STATUS_VEICULOS else 0
                            novo_status = st.selectbox("Alterar status", STATUS_VEICULOS[:2], index=min(indice, 1), key=f"status_{veiculo['id']}")
                            if st.button("Salvar status", key=f"salvar_status_{veiculo['id']}", use_container_width=True):
                                try:
                                    atualizar_veiculo(veiculo["id"], {"status": novo_status})
                                    st.success("Status atualizado!")
                                    st.rerun()
                                except Exception as erro:
                                    st.error("Não foi possível atualizar o status.")
                                    st.code(str(erro))
                        st.checkbox("Confirmar exclusão", key=f"confirmar_{veiculo['id']}")
                        confirmar = st.session_state.get(f"confirmar_{veiculo['id']}", False)
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

# Create vehicle
elif pagina == "Cadastrar veículo":
    st.subheader("Cadastrar veículo")
    with st.form("form_cadastrar_veiculo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        marca = c1.text_input("Marca *", placeholder="Ex.: Toyota")
        modelo = c2.text_input("Modelo *", placeholder="Ex.: Corolla XEi")
        c3, c4 = st.columns(2)
        ano = c3.number_input("Ano *", min_value=1900, max_value=2100, value=2020, step=1)
        quilometragem = c4.number_input("Quilometragem (km) *", min_value=0, value=0, step=1000)
        preco_texto = campo_preco("Preço anunciado (R$) *", 0, "preco_cadastro")
        custo_texto = campo_preco("Custo de compra (R$)", 0, "custo_cadastro")
        status = st.selectbox("Status", STATUS_VEICULOS[:2])
        foto = st.file_uploader("Foto do veículo (opcional)", type=["jpg", "jpeg", "png", "webp"])
        enviar = st.form_submit_button("Cadastrar veículo", use_container_width=True)
    if enviar:
        if not marca.strip() or not modelo.strip():
            st.error("Preencha a marca e o modelo.")
        else:
            try:
                preco = interpretar_preco(preco_texto)
                custo = interpretar_preco(custo_texto or "0")
                if preco <= 0:
                    raise ValueError("Informe um preço anunciado maior que zero.")
                with st.spinner("Salvando veículo..."):
                    caminho_foto = salvar_foto(foto) if foto is not None else None
                    dados = {"concessionaria_id": concessionaria_id, "marca": marca.strip(), "modelo": modelo.strip(),
                             "ano": int(ano), "quilometragem": int(quilometragem), "preco": preco,
                             "custo_compra": custo, "status": status, "foto_url": caminho_foto}
                    supabase.table("veiculos").insert(dados).execute()
                st.success("Veículo cadastrado com sucesso!")
                st.rerun()
            except ValueError as erro:
                st.error(str(erro))
            except Exception as erro:
                st.error("Não foi possível cadastrar o veículo. Confira se executou o SQL de configuração.")
                st.code(str(erro))

# Edit vehicle
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
            ano_ed = c3.number_input("Ano *", min_value=1900, max_value=2100, value=max(1900, min(2100, int(escolhido.get("ano") or 2020))), step=1)
            km_ed = c4.number_input("Quilometragem (km) *", min_value=0, value=max(0, int(escolhido.get("quilometragem") or 0)), step=1000)
            preco_ed_texto = campo_preco("Preço anunciado (R$) *", escolhido.get("preco") or 0, f"preco_ed_{escolhido['id']}")
            custo_ed_texto = campo_preco("Custo de compra (R$)", escolhido.get("custo_compra") or 0, f"custo_ed_{escolhido['id']}")
            atual = escolhido.get("status")
            indice = STATUS_VEICULOS.index(atual) if atual in STATUS_VEICULOS else 0
            status_ed = st.selectbox("Status", STATUS_VEICULOS, index=indice)
            foto_nova = st.file_uploader("Substituir foto (opcional)", type=["jpg", "jpeg", "png", "webp"])
            salvar_edicao = st.form_submit_button("Salvar alterações", use_container_width=True)
        if salvar_edicao:
            if not marca_ed.strip() or not modelo_ed.strip():
                st.error("Preencha a marca e o modelo.")
            else:
                try:
                    preco_ed = interpretar_preco(preco_ed_texto)
                    custo_ed = interpretar_preco(custo_ed_texto or "0")
                    if preco_ed <= 0:
                        raise ValueError("Informe um preço anunciado maior que zero.")
                    caminho_foto_ed = escolhido.get("foto_url")
                    if foto_nova is not None:
                        caminho_foto_ed = salvar_foto(foto_nova)
                    dados_ed = {"marca": marca_ed.strip(), "modelo": modelo_ed.strip(), "ano": int(ano_ed),
                                "quilometragem": int(km_ed), "preco": preco_ed, "custo_compra": custo_ed,
                                "status": status_ed, "foto_url": caminho_foto_ed}
                    atualizar_veiculo(escolhido["id"], dados_ed)
                    st.success("Veículo atualizado com sucesso!")
                    st.rerun()
                except ValueError as erro:
                    st.error(str(erro))
                except Exception as erro:
                    st.error("Não foi possível salvar as alterações.")
                    st.code(str(erro))

# Register sale
elif pagina == "Registrar venda":
    st.subheader("💰 Registrar venda")
    st.caption("Ao concluir, o veículo será marcado como Vendido e a venda ficará registrada no histórico.")
    try:
        veiculos = [v for v in buscar_veiculos() if v.get("status") in ("Disponível", "Reservado")]
    except Exception as erro:
        st.error("Não foi possível carregar o estoque.")
        st.code(str(erro))
        veiculos = []
    if not veiculos:
        st.info("Não há veículos disponíveis ou reservados para vender.")
    else:
        opcoes = {f"{v.get('marca','')} {v.get('modelo','')} — {v.get('ano','')} | anunciado: {moeda(v.get('preco'))}": v for v in veiculos}
        label = st.selectbox("Veículo vendido", list(opcoes.keys()))
        escolhido = opcoes[label]
        with st.container(border=True):
            st.markdown(f"### {escolhido.get('marca','')} {escolhido.get('modelo','')}")
            st.write(f"Preço anunciado: **{moeda(escolhido.get('preco'))}**")
            st.write(f"Custo de compra: **{moeda(escolhido.get('custo_compra'))}**")
        with st.form("form_registrar_venda"):
            preco_venda_texto = campo_preco("Preço final de venda (R$) *", escolhido.get("preco") or 0, f"preco_venda_{escolhido['id']}")
            custo_venda_texto = campo_preco("Custo de compra confirmado (R$)", escolhido.get("custo_compra") or 0, f"custo_venda_{escolhido['id']}")
            data_venda = st.date_input("Data da venda", value=date.today())
            observacoes = st.text_area("Observações (opcional)", placeholder="Ex.: forma de pagamento, referência interna...")
            confirmar_venda = st.checkbox("Confirmo que esta venda foi realizada.")
            enviar_venda = st.form_submit_button("Registrar venda", use_container_width=True)
        if enviar_venda:
            if not confirmar_venda:
                st.error("Marque a confirmação antes de registrar a venda.")
            else:
                try:
                    preco_venda = interpretar_preco(preco_venda_texto)
                    custo_venda = interpretar_preco(custo_venda_texto or "0")
                    if preco_venda <= 0:
                        raise ValueError("O preço final da venda deve ser maior que zero.")
                    lucro_bruto = round(preco_venda - custo_venda, 2)
                    dados_venda = {"concessionaria_id": concessionaria_id, "veiculo_id": escolhido["id"],
                                   "marca": escolhido.get("marca", ""), "modelo": escolhido.get("modelo", ""),
                                   "ano": int(escolhido.get("ano") or 0), "preco_venda": preco_venda,
                                   "custo_compra": custo_venda, "lucro_bruto": lucro_bruto,
                                   "data_venda": data_venda.isoformat(), "observacoes": observacoes.strip() or None}
                    # Atualiza o status primeiro; se o registro da venda falhar, tenta reverter o status.
                    atualizar_veiculo(escolhido["id"], {"status": "Vendido", "custo_compra": custo_venda})
                    try:
                        supabase.table("vendas").insert(dados_venda).execute()
                    except Exception:
                        try:
                            atualizar_veiculo(escolhido["id"], {"status": escolhido.get("status", "Disponível")})
                        except Exception:
                            pass
                        raise
                    st.success(f"Venda registrada! Faturamento: {moeda(preco_venda)} • Lucro bruto estimado: {moeda(lucro_bruto)}")
                    st.rerun()
                except ValueError as erro:
                    st.error(str(erro))
                except Exception as erro:
                    st.error("Não foi possível registrar a venda. Confira a tabela vendas e a coluna custo_compra no Supabase.")
                    st.code(str(erro))

# Sales history
elif pagina == "Histórico de vendas":
    st.subheader("📜 Histórico de vendas")
    hoje = date.today()
    c1, c2 = st.columns(2)
    inicio = c1.date_input("De", value=hoje.replace(day=1), key="hist_inicio")
    fim = c2.date_input("Até", value=hoje, key="hist_fim")
    if inicio > fim:
        st.error("A data inicial não pode ser depois da data final.")
    else:
        try:
            vendas = buscar_vendas(inicio, fim)
            st.metric("Vendas no período", len(vendas))
            st.metric("Faturamento no período", moeda(sum(float(v.get("preco_venda") or 0) for v in vendas)))
            if vendas:
                linhas = [{"Data": v.get("data_venda"), "Marca": v.get("marca", ""), "Modelo": v.get("modelo", ""),
                           "Ano": v.get("ano", ""), "Preço de venda": moeda(v.get("preco_venda")),
                           "Custo de compra": moeda(v.get("custo_compra")), "Lucro bruto": moeda(v.get("lucro_bruto")),
                           "Observações": v.get("observacoes") or ""} for v in vendas]
                st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)
                csv = pd.DataFrame(linhas).to_csv(index=False).encode("utf-8-sig")
                st.download_button("Baixar histórico em CSV", data=csv, file_name=f"historico_vendas_{inicio}_{fim}.csv", mime="text/csv")
            else:
                st.info("Nenhuma venda encontrada nesse período.")
        except Exception as erro:
            st.error("Não foi possível carregar o histórico. Confirme se executou o SQL de configuração.")
            st.code(str(erro))

# Reports
elif pagina == "Relatórios":
    st.subheader("📊 Relatórios de vendas")
    hoje = date.today()
    c1, c2 = st.columns(2)
    inicio_rel = c1.date_input("Data inicial", value=hoje.replace(day=1), key="rel_inicio")
    fim_rel = c2.date_input("Data final", value=hoje, key="rel_fim")
    if inicio_rel > fim_rel:
        st.error("A data inicial não pode ser depois da data final.")
    else:
        try:
            vendas_rel = buscar_vendas(inicio_rel, fim_rel)
            faturamento_rel = sum(float(v.get("preco_venda") or 0) for v in vendas_rel)
            custo_rel = sum(float(v.get("custo_compra") or 0) for v in vendas_rel)
            lucro_rel = sum(float(v.get("lucro_bruto") or 0) for v in vendas_rel)
            a, b, c = st.columns(3)
            a.metric("Quantidade de vendas", len(vendas_rel))
            b.metric("Faturamento", moeda(faturamento_rel))
            c.metric("Lucro bruto estimado", moeda(lucro_rel))
            st.caption("Lucro bruto estimado = preço final de venda − custo de compra. Não desconta impostos, comissões, manutenção, financiamento ou outras despesas.")
            if vendas_rel:
                df = pd.DataFrame([{"Mês": str(v.get("data_venda", ""))[:7], "Veículo": f"{v.get('marca','')} {v.get('modelo','')}",
                                    "Faturamento": float(v.get("preco_venda") or 0), "Custo": float(v.get("custo_compra") or 0),
                                    "Lucro bruto": float(v.get("lucro_bruto") or 0)} for v in vendas_rel])
                mensal = df.groupby("Mês", as_index=False).agg({"Faturamento": "sum", "Custo": "sum", "Lucro bruto": "sum"})
                st.markdown("### Resumo mensal")
                st.dataframe(pd.DataFrame([{"Mês": r["Mês"], "Faturamento": moeda(r["Faturamento"]), "Custo": moeda(r["Custo"]), "Lucro bruto": moeda(r["Lucro bruto"])} for _, r in mensal.iterrows()]), use_container_width=True, hide_index=True)
                st.markdown("### Vendas no período")
                st.dataframe(pd.DataFrame([{"Data": v.get("data_venda"), "Veículo": f"{v.get('marca','')} {v.get('modelo','')}",
                                            "Venda": moeda(v.get("preco_venda")), "Custo": moeda(v.get("custo_compra")),
                                            "Lucro bruto": moeda(v.get("lucro_bruto"))} for v in vendas_rel]), use_container_width=True, hide_index=True)
                csv_rel = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("Baixar dados do relatório (CSV)", data=csv_rel, file_name=f"relatorio_vendas_{inicio_rel}_{fim_rel}.csv", mime="text/csv")
            else:
                st.info("Não há vendas no período selecionado.")
        except Exception as erro:
            st.error("Não foi possível gerar o relatório. Confirme se executou o SQL de configuração.")
            st.code(str(erro))

st.divider()
st.caption("Sistema Automotivo Pro • Gestão de veículos e vendas")
