import streamlit as st
import pandas as pd
import plotly.express as px
from style import ORIGEM_COLORS, style_chart


def render_leads(supabase):
    st.subheader("Leads")

    try:
        result = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        leads = result.data
    except Exception as e:
        st.error(f"Erro ao carregar leads: {e}")
        leads = []

    if not leads:
        st.info("Nenhum lead registrado ainda.")
        return

    df = pd.DataFrame(leads)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total de leads", len(df))
    col_b.metric("Strategic Intelligence", (df["origem"] == "strategic-intelligence").sum())
    col_c.metric("Human Performance", (df["origem"] == "human-performance").sum())

    st.markdown("---")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        empresas = ["Todas"] + sorted(df["empresa"].dropna().unique().tolist())
        filtro_empresa = st.selectbox("Filtrar por empresa", empresas)
    with col_f2:
        areas_unicas = set()
        for areas in df["area_interesse"].dropna():
            for a in areas.split(","):
                areas_unicas.add(a.strip())
        filtro_area = st.selectbox("Filtrar por área de interesse", ["Todas"] + sorted(areas_unicas))

    df_filtrado = df.copy()
    if filtro_empresa != "Todas":
        df_filtrado = df_filtrado[df_filtrado["empresa"] == filtro_empresa]
    if filtro_area != "Todas":
        df_filtrado = df_filtrado[
            df_filtrado["area_interesse"].fillna("").str.contains(filtro_area, regex=False)
        ]

    st.markdown("---")

    col_g1, col_g2 = st.columns([1, 2])

    with col_g1:
        st.markdown("**Origem dos leads**")
        origem_counts = df_filtrado["origem"].value_counts().reset_index()
        origem_counts.columns = ["origem", "quantidade"]
        fig_pizza = px.pie(
            origem_counts, names="origem", values="quantidade",
            color="origem",
            color_discrete_map=ORIGEM_COLORS,
            hole=0.4,
        )
        style_chart(fig_pizza)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_g2:
        st.markdown("**Leads por empresa**")
        empresa_origem_counts = (
            df_filtrado.dropna(subset=["empresa"])
            .groupby(["empresa", "origem"])
            .size()
            .reset_index(name="quantidade")
        )
        ordem_empresas = (
            empresa_origem_counts.groupby("empresa")["quantidade"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )

        fig_colunas = px.bar(
            empresa_origem_counts,
            x="empresa",
            y="quantidade",
            color="origem",
            color_discrete_map=ORIGEM_COLORS,
            barmode="stack",
            category_orders={"empresa": ordem_empresas},
        )
        style_chart(fig_colunas, grid_axes=True)
        st.plotly_chart(fig_colunas, use_container_width=True)

    st.markdown("---")
    st.markdown(f"**Lista de leads** ({len(df_filtrado)} resultado(s))")

    colunas_exibir = ["created_at", "nome", "email", "telefone", "empresa", "area_interesse", "origem", "status"]
    colunas_existentes = [c for c in colunas_exibir if c in df_filtrado.columns]
    st.dataframe(
        df_filtrado[colunas_existentes].sort_values("created_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )