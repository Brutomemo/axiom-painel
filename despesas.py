import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

CATEGORIAS_DESPESA = [
    "Assinaturas e Plataformas (Fixo)",
    "Equipamentos e Material de Escritório",
    "Serviços de Contabilidade",
    "Serviços Jurídicos",
    "Serviços de Terceiros",
    "Marketing",
    "Outro",
]

FREQUENCIAS = ["Mensal", "Anual"]


def render_despesas(supabase):
    st.subheader("Despesas Gerais da Empresa")
    st.caption("Equipamentos, internet, telefone, plataformas, IAs e demais custos operacionais — independentes de projetos de clientes.")

    with st.expander("➕ Nova despesa", expanded=False):
        with st.form("nova_despesa", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categoria = st.selectbox("Categoria", CATEGORIAS_DESPESA)
                descricao = st.text_input("Descrição", placeholder="Ex.: Plano Streamlit Cloud, Notebook Dell...")
                fornecedor = st.text_input("Fornecedor", placeholder="Ex.: Vercel, Vivo, Apple...")
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
                data_despesa = st.date_input("Data da despesa", value=date.today())
                recorrente = st.checkbox("Despesa recorrente")
                frequencia = st.selectbox("Frequência", FREQUENCIAS, index=0, disabled=not recorrente)

            observacoes = st.text_area("Observações")
            submitted = st.form_submit_button("Salvar despesa")

            if submitted:
                if not descricao or valor <= 0:
                    st.warning("Informe ao menos a descrição e um valor maior que zero.")
                else:
                    try:
                        supabase.table("despesas_gerais").insert({
                            "categoria": categoria,
                            "descricao": descricao,
                            "fornecedor": fornecedor,
                            "valor": valor,
                            "data_despesa": data_despesa.isoformat(),
                            "recorrente": recorrente,
                            "frequencia": frequencia if recorrente else "Único",
                            "observacoes": observacoes,
                        }).execute()
                        st.success("Despesa registrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    st.markdown("---")

    try:
        result = supabase.table("despesas_gerais").select("*").order("data_despesa", desc=True).execute()
        despesas = result.data
    except Exception as e:
        st.error(f"Erro ao carregar despesas: {e}")
        despesas = []

    if not despesas:
        st.info("Nenhuma despesa registrada ainda.")
        return

    df = pd.DataFrame(despesas)
    df["data_despesa"] = pd.to_datetime(df["data_despesa"], errors="coerce")

    total_despesas = df["valor"].fillna(0).sum()
    recorrentes_mensais = df[(df["recorrente"] == True) & (df["frequencia"] == "Mensal")]["valor"].fillna(0).sum()
    recorrentes_anuais = df[(df["recorrente"] == True) & (df["frequencia"] == "Anual")]["valor"].fillna(0).sum()

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total de despesas registradas", f"R$ {total_despesas:,.2f}")
    col_b.metric("Custo fixo mensal recorrente", f"R$ {recorrentes_mensais:,.2f}")
    col_c.metric("Custo fixo anual recorrente", f"R$ {recorrentes_anuais:,.2f}")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Despesas por categoria**")
        cat_counts = df.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
        fig_cat = px.bar(cat_counts, x="categoria", y="valor", color_discrete_sequence=["#06b6d4"])
        fig_cat.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            xaxis=dict(gridcolor="#1a2035"), yaxis=dict(gridcolor="#1a2035"),
            height=320,
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_g2:
        st.markdown("**Despesas ao longo do tempo**")
        df_tempo = df.dropna(subset=["data_despesa"]).copy()
        if not df_tempo.empty:
            df_tempo["mes"] = df_tempo["data_despesa"].dt.to_period("M").astype(str)
            mensal = df_tempo.groupby("mes")["valor"].sum().reset_index()
            fig_tempo = px.line(mensal, x="mes", y="valor", color_discrete_sequence=["#94a3b8"], markers=True)
            fig_tempo.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                xaxis=dict(gridcolor="##94a3b8"), yaxis=dict(gridcolor="#94a3b8"),
                height=320,
            )
            st.plotly_chart(fig_tempo, use_container_width=True)
        else:
            st.info("Sem datas suficientes para a linha do tempo.")

    st.markdown("**Detalhamento por fornecedor dentro de cada categoria**")
    detalhe = df.groupby(["categoria", "fornecedor"])["valor"].sum().reset_index()
    detalhe = detalhe.sort_values(["categoria", "valor"], ascending=[True, False])
    detalhe.columns = ["Categoria", "Fornecedor", "Total (R$)"]
    st.dataframe(detalhe, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### ✏️ Editar ou excluir despesa")

    opcoes = {f"{d['id']} — {d['descricao']} (R$ {float(d.get('valor') or 0):.2f})": d for d in despesas}
    selecao = st.selectbox("Selecione a despesa", options=["—"] + list(opcoes.keys()), key="edit_despesa_select")

    if selecao != "—":
        despesa = opcoes[selecao]
        with st.form("editar_despesa"):
            col1, col2 = st.columns(2)
            with col1:
                idx_cat = CATEGORIAS_DESPESA.index(despesa["categoria"]) if despesa.get("categoria") in CATEGORIAS_DESPESA else 0
                categoria_e = st.selectbox("Categoria", CATEGORIAS_DESPESA, index=idx_cat)
                descricao_e = st.text_input("Descrição", value=despesa.get("descricao") or "")
                fornecedor_e = st.text_input("Fornecedor", value=despesa.get("fornecedor") or "")
            with col2:
                valor_e = st.number_input("Valor (R$)", min_value=0.0, step=10.0, value=float(despesa.get("valor") or 0))
                data_despesa_e = st.date_input(
                    "Data da despesa",
                    value=pd.to_datetime(despesa["data_despesa"]).date() if despesa.get("data_despesa") else date.today()
                )
                recorrente_e = st.checkbox("Despesa recorrente", value=despesa.get("recorrente") or False)
                idx_freq = FREQUENCIAS.index(despesa["frequencia"]) if despesa.get("frequencia") in FREQUENCIAS else 0
                frequencia_e = st.selectbox("Frequência", FREQUENCIAS, index=idx_freq, disabled=not recorrente_e)

            observacoes_e = st.text_area("Observações", value=despesa.get("observacoes") or "")

            col_save, col_delete = st.columns(2)
            salvar = col_save.form_submit_button("💾 Salvar alterações")
            deletar = col_delete.form_submit_button("🗑️ Excluir despesa")

            if salvar:
                try:
                    supabase.table("despesas_gerais").update({
                        "categoria": categoria_e,
                        "descricao": descricao_e,
                        "fornecedor": fornecedor_e,
                        "valor": valor_e,
                        "data_despesa": data_despesa_e.isoformat(),
                        "recorrente": recorrente_e,
                        "frequencia": frequencia_e if recorrente_e else "Único",
                        "observacoes": observacoes_e,
                    }).eq("id", despesa["id"]).execute()
                    st.success("Despesa atualizada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")

            if deletar:
                try:
                    supabase.table("despesas_gerais").delete().eq("id", despesa["id"]).execute()
                    st.success("Despesa excluída.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")

    st.markdown("---")
    st.markdown(f"**Histórico completo** ({len(df)} despesa(s))")
    colunas_exibir = ["data_despesa", "categoria", "descricao", "fornecedor", "valor", "recorrente", "frequencia"]
    colunas_existentes = [c for c in colunas_exibir if c in df.columns]
    st.dataframe(df[colunas_existentes].sort_values("data_despesa", ascending=False), use_container_width=True, hide_index=True)    