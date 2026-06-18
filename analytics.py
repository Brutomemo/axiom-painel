import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date
from style import FINANCE_COLORS, TREND_DATA_COLOR, TREND_LINE_COLOR, style_chart


def render_analytics(supabase):
    st.subheader("Analytics — Serviços Prestados")

    try:
        result = supabase.table("servicos_prestados").select("*").order("created_at", desc=True).execute()
        servicos = result.data
    except Exception as e:
        st.error(f"Erro ao carregar serviços: {e}")
        servicos = []

    if not servicos:
        st.info("Nenhum serviço registrado ainda. Cadastre na aba Serviços.")
        return

    df = pd.DataFrame(servicos)

    for col in ["data_solicitacao", "data_entrega_1", "data_entrega_2_prevista", "data_entrega_2_real"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    st.markdown("### Filtros")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_status = st.selectbox(
            "Status", ["Todos"] + sorted(df["status"].dropna().unique().tolist())
        )
    with col_f2:
        filtro_origem = st.selectbox(
            "Divisão", ["Todas", "strategic-intelligence", "human-performance"]
        )
    with col_f3:
        filtro_empresa = st.selectbox(
            "Empresa", ["Todas"] + sorted(df["empresa"].dropna().unique().tolist())
        )

    df_f = df.copy()
    if filtro_status != "Todos":
        df_f = df_f[df_f["status"] == filtro_status]
    if filtro_origem != "Todas":
        df_f = df_f[df_f["origem"] == filtro_origem]
    if filtro_empresa != "Todas":
        df_f = df_f[df_f["empresa"] == filtro_empresa]

    st.markdown("---")

    # ── MÉTRICAS PRINCIPAIS ──
    st.markdown("### Visão geral")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Total de contratos", len(df_f))
    col_b.metric("Em andamento", (df_f["status"] == "em andamento").sum())
    col_c.metric("Em atraso", (df_f["status"] == "em atraso").sum())
    col_d.metric("Concluídos", (df_f["status"] == "concluído").sum())

    st.markdown("### Financeiro")

    try:
        despesas_gerais_result = supabase.table("despesas_gerais").select("valor").execute()
        total_despesas_gerais = sum(d.get("valor") or 0 for d in despesas_gerais_result.data)
    except Exception:
        total_despesas_gerais = 0

    bruto = df_f["preco_cobrado"].fillna(0).sum()
    despesas_projetos = df_f["custos_projeto"].fillna(0).sum()
    despesas = despesas_projetos + total_despesas_gerais
    liquido = bruto - despesas
    mrr = df_f["mensalidade"].fillna(0).sum()
    margem = (liquido / bruto * 100) if bruto > 0 else 0
    ticket_medio = bruto / len(df_f) if len(df_f) > 0 else 0

    col_e, col_f, col_g, col_h = st.columns(4)
    col_e.metric("Faturamento bruto", f"R$ {bruto:,.2f}")
    col_f.metric(
        "Despesas totais", f"R$ {despesas:,.2f}",
        help=f"Projetos: R$ {despesas_projetos:,.2f} + Operação da empresa: R$ {total_despesas_gerais:,.2f}"
    )
    col_g.metric("Lucro líquido", f"R$ {liquido:,.2f}")
    col_h.metric("Receita recorrente (MRR)", f"R$ {mrr:,.2f}")

    col_i, col_j = st.columns(2)
    col_i.metric("Margem de lucro", f"{margem:.1f}%")
    col_j.metric("Ticket médio", f"R$ {ticket_medio:,.2f}")

    st.markdown("---")

    # ── GRÁFICOS ──
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Distribuição por status**")
        status_counts = df_f["status"].value_counts().reset_index()
        status_counts.columns = ["status", "quantidade"]
        cores_status = {
            "em andamento": "#06b6d4",
            "em atraso": "#ef4444",
            "concluído": "#22c55e",
        }
        fig_status = px.pie(
            status_counts, names="status", values="quantidade",
            color="status", color_discrete_map=cores_status, hole=0.4,
        )
        fig_status.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", height=320,
            legend=dict(font=dict(color="#94a3b8")),
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with col_g2:
        st.markdown("**Origem dos contratos**")
        origem_counts = df_f["origem"].value_counts().reset_index()
        origem_counts.columns = ["origem", "quantidade"]
        fig_origem = px.pie(
            origem_counts, names="origem", values="quantidade",
            color="origem",
            color_discrete_map={
                "strategic-intelligence": "#d47406",
                "human-performance": "#11c5fc",
            },
            hole=0.4,
        )
        fig_origem.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", height=320,
            legend=dict(font=dict(color="#94a3b8")),
        )
        st.plotly_chart(fig_origem, use_container_width=True)

    st.markdown("**Faturamento, custos e lucro por empresa**")
    fin_por_empresa = df_f.groupby("empresa", dropna=True).agg(
        faturamento=("preco_cobrado", "sum"),
        custos=("custos_projeto", "sum"),
        lucro=("lucro", "sum"),
    ).reset_index().sort_values("faturamento", ascending=False)

    if not fin_por_empresa.empty:
        fin_melt = fin_por_empresa.melt(
            id_vars=["empresa"],
            value_vars=["faturamento", "custos", "lucro"],
            var_name="metrica",
            value_name="valor",
        )
        fin_melt["metrica"] = fin_melt["metrica"].map(
            {"faturamento": "Faturamento", "custos": "Custos", "lucro": "Lucro"}
        )

        fig_fin = px.bar(
            fin_melt,
            x="empresa",
            y="valor",
            color="metrica",
            barmode="group",
            color_discrete_map=FINANCE_COLORS,
            labels={"valor": "Valor (R$)", "metrica": "", "empresa": "Empresa"},
            category_orders={"empresa": fin_por_empresa["empresa"].tolist()},
        )
        style_chart(fig_fin, grid_axes=True)
        st.plotly_chart(fig_fin, use_container_width=True)

    # ── LINHA DO TEMPO DE FATURAMENTO ──
    st.markdown("**Faturamento ao longo do tempo**")
    df_tempo = df_f.dropna(subset=["data_solicitacao"]).copy()
    if not df_tempo.empty:
        df_tempo["mes"] = df_tempo["data_solicitacao"].dt.to_period("M").astype(str)
        faturamento_mensal = (
            df_tempo.groupby("mes")["preco_cobrado"]
            .sum()
            .reset_index()
            .sort_values("mes")
        )

        fig_tempo = go.Figure()
        fig_tempo.add_trace(
            go.Scatter(
                x=faturamento_mensal["mes"],
                y=faturamento_mensal["preco_cobrado"],
                mode="lines+markers",
                name="Faturamento",
                line=dict(color=TREND_DATA_COLOR, width=2),
                marker=dict(color=TREND_DATA_COLOR, size=7),
            )
        )

        if len(faturamento_mensal) >= 2:
            x_numeric = np.arange(len(faturamento_mensal))
            coef = np.polyfit(x_numeric, faturamento_mensal["preco_cobrado"], 1)
            tendencia = np.poly1d(coef)(x_numeric)
            fig_tempo.add_trace(
                go.Scatter(
                    x=faturamento_mensal["mes"],
                    y=tendencia,
                    mode="lines",
                    name="Tendência",
                    line=dict(color=TREND_LINE_COLOR, width=2, dash="dash"),
                )
            )

        fig_tempo.update_layout(
            xaxis_title="Mês",
            yaxis_title="Faturamento (R$)",
        )
        style_chart(fig_tempo, grid_axes=True)
        st.plotly_chart(fig_tempo, use_container_width=True)
    else:
        st.info("Sem datas de solicitação suficientes para a linha do tempo.")

    st.markdown("---")

    # ── CONTROLE DE PRAZOS ──
    st.markdown("### Controle de prazos")

    df_prazos = df_f[df_f["status"] != "concluído"].copy()
    if not df_prazos.empty:
        hoje = pd.Timestamp(date.today())

        def dias_restantes(row):
            if pd.isna(row["data_entrega_2_prevista"]):
                return None
            return (row["data_entrega_2_prevista"] - hoje).days

        df_prazos["dias_restantes"] = df_prazos.apply(dias_restantes, axis=1)
        df_prazos = df_prazos.sort_values("dias_restantes", na_position="last")

        for _, row in df_prazos.iterrows():
            dias = row["dias_restantes"]
            if dias is None:
                cor, texto_prazo = "#475569", "Sem prazo definido"
            elif dias < 0:
                cor, texto_prazo = "#ef4444", f"{abs(dias)} dia(s) em atraso"
            elif dias <= 7:
                cor, texto_prazo = "#f59e0b", f"{dias} dia(s) restante(s)"
            else:
                cor, texto_prazo = "#22c55e", f"{dias} dia(s) restante(s)"

            st.markdown(
                f'<div style="background:#0d0f18;border:1px solid #1a2035;'
                f'border-left:3px solid {cor};border-radius:0 8px 8px 0;'
                f'padding:12px 16px;margin-bottom:8px;display:flex;'
                f'justify-content:space-between;align-items:center;">'
                f'<div><strong style="color:#e2e8f0;">{row.get("empresa", "—")}</strong> '
                f'<span style="color:#64748b;">— {row.get("tipo_servico", "—")}</span></div>'
                f'<div style="color:{cor};font-weight:600;">{texto_prazo}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Nenhum serviço em aberto com esses filtros.")

    st.markdown("---")

    st.markdown("---")
    st.markdown("### Lucro líquido real da empresa")

    try:
        despesas_result = supabase.table("despesas_gerais").select("valor").execute()
        total_despesas_gerais = sum(d.get("valor") or 0 for d in despesas_result.data)
    except Exception:
        total_despesas_gerais = 0

    lucro_real = liquido - total_despesas_gerais

    col_x, col_y, col_z = st.columns(3)
    col_x.metric("Lucro dos projetos", f"R$ {liquido:,.2f}")
    col_y.metric("Despesas gerais da empresa", f"R$ {total_despesas_gerais:,.2f}")
    col_z.metric("Lucro líquido real", f"R$ {lucro_real:,.2f}")

    # ── TABELA DETALHADA ──
    st.markdown(f"**Detalhamento** ({len(df_f)} serviço(s))")
    colunas_exibir = [
        "empresa", "responsavel", "tipo_servico", "origem", "status",
        "data_solicitacao", "data_entrega_2_prevista",
        "preco_cobrado", "custos_projeto", "lucro", "mensalidade",
        "numero_contrato",
    ]
    colunas_existentes = [c for c in colunas_exibir if c in df_f.columns]
    st.dataframe(df_f[colunas_existentes], use_container_width=True, hide_index=True)