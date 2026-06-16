import streamlit as st
import pandas as pd
import plotly.express as px


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
            color_discrete_map={
                "strategic-intelligence": "#d47406",
                "human-performance": "#11c5fc",
            },
            hole=0.4,
        )
        fig_pizza.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            legend=dict(font=dict(color="#94a3b8")),
            height=320,
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_g2:
        st.markdown("**Leads por empresa**")
        empresa_counts = df_filtrado["empresa"].dropna().value_counts().reset_index()
        empresa_counts.columns = ["empresa", "quantidade"]

        altura_dinamica = max(320, 28 * len(empresa_counts))

        fig_barras = px.bar(
            empresa_counts.sort_values("quantidade", ascending=True),
            x="quantidade", y="empresa",
            orientation="h",
            color_discrete_sequence=["#06b6d4"],
        )
        fig_barras.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            xaxis=dict(gridcolor="#1a2035"),
            yaxis=dict(gridcolor="#1a2035"),
            height=altura_dinamica,
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")
    st.markdown(f"**Lista de leads** ({len(df_filtrado)} resultado(s))")

    colunas_exibir = ["created_at", "nome", "email", "telefone", "empresa", "area_interesse", "origem", "status"]
    colunas_existentes = [c for c in colunas_exibir if c in df_filtrado.columns]
    st.dataframe(
        df_filtrado[colunas_existentes].sort_values("created_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )