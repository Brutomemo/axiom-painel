import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, time

TIPOS_COMPROMISSO = [
    "Reunião", "Atendimento a Cliente", "Desenvolvimento",
    "Diagnóstico/Treinamento", "Administrativo", "Outro",
]
STATUS_COMPROMISSO = ["Agendado", "Em andamento", "Concluído", "Cancelado"]


def calcular_duracao_horas(hora_inicio, hora_fim):
    if not hora_inicio or not hora_fim:
        return None
    inicio = datetime.combine(date.today(), hora_inicio)
    fim = datetime.combine(date.today(), hora_fim)
    if fim < inicio:
        fim += pd.Timedelta(days=1)
    return round((fim - inicio).total_seconds() / 3600, 2)


def render_agenda(supabase):
    st.subheader("Agenda dos Líderes")
    st.caption("Registre compromissos, reuniões e tarefas, e acompanhe o tempo de empenho em cada atividade.")

    try:
        servicos_result = supabase.table("servicos_prestados").select("id, empresa, tipo_servico").execute()
        servicos_opcoes = {f"{s['id']} — {s['empresa']} ({s['tipo_servico']})": s["id"] for s in servicos_result.data}
    except Exception:
        servicos_opcoes = {}

    with st.expander("➕ Novo compromisso", expanded=False):
        with st.form("novo_compromisso", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                lider = st.text_input("Líder responsável", placeholder="Ex.: Marcos Batista")
                titulo = st.text_input("Título / descrição", placeholder="Ex.: Reunião de diagnóstico com Empresa X")
                tipo = st.selectbox("Tipo", TIPOS_COMPROMISSO)
                servico_label = st.selectbox("Vincular a um serviço (opcional)", ["—"] + list(servicos_opcoes.keys()))
            with col2:
                data_compromisso = st.date_input("Data", value=date.today())
                hora_inicio = st.time_input("Hora de início", value=time(9, 0))
                hora_fim = st.time_input("Hora de término", value=time(10, 0))
                status = st.selectbox("Status", STATUS_COMPROMISSO)

            observacoes = st.text_area("Observações")
            submitted = st.form_submit_button("Salvar compromisso")

            if submitted:
                if not lider or not titulo:
                    st.warning("Informe ao menos o líder responsável e o título do compromisso.")
                else:
                    servico_id = servicos_opcoes.get(servico_label) if servico_label != "—" else None
                    try:
                        supabase.table("agenda_compromissos").insert({
                            "lider": lider,
                            "titulo": titulo,
                            "tipo": tipo,
                            "data": data_compromisso.isoformat(),
                            "hora_inicio": hora_inicio.isoformat(),
                            "hora_fim": hora_fim.isoformat(),
                            "status": status,
                            "servico_id": servico_id,
                            "observacoes": observacoes,
                        }).execute()
                        st.success("Compromisso registrado!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    st.markdown("---")

    try:
        result = supabase.table("agenda_compromissos").select("*").order("data", desc=True).execute()
        compromissos = result.data
    except Exception as e:
        st.error(f"Erro ao carregar agenda: {e}")
        compromissos = []

    if not compromissos:
        st.info("Nenhum compromisso registrado ainda.")
        return

    df = pd.DataFrame(compromissos)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    def calc_horas(row):
        try:
            hi = datetime.strptime(str(row["hora_inicio"]), "%H:%M:%S").time()
            hf = datetime.strptime(str(row["hora_fim"]), "%H:%M:%S").time()
            return calcular_duracao_horas(hi, hf)
        except Exception:
            return None

    df["horas"] = df.apply(calc_horas, axis=1)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total de compromissos", len(df))
    col_b.metric("Horas totais registradas", f"{df['horas'].fillna(0).sum():.1f}h")
    col_c.metric("Concluídos", (df["status"] == "Concluído").sum())

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_lider = st.selectbox("Filtrar por líder", ["Todos"] + sorted(df["lider"].dropna().unique().tolist()))
    with col_f2:
        filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos"] + sorted(df["tipo"].dropna().unique().tolist()))

    df_f = df.copy()
    if filtro_lider != "Todos":
        df_f = df_f[df_f["lider"] == filtro_lider]
    if filtro_tipo != "Todos":
        df_f = df_f[df_f["tipo"] == filtro_tipo]

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Horas dedicadas por líder**")
        horas_lider = df_f.groupby("lider")["horas"].sum().reset_index().sort_values("horas", ascending=True)
        fig_lider = px.bar(
            horas_lider, x="horas", y="lider", orientation="h",
            color_discrete_sequence=["#06b6d4"],
        )
        fig_lider.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            xaxis=dict(gridcolor="#1a2035"), yaxis=dict(gridcolor="#1a2035"),
            height=max(280, 32 * len(horas_lider)),
        )
        st.plotly_chart(fig_lider, use_container_width=True)

    with col_g2:
        st.markdown("**Compromissos por tipo**")
        tipo_counts = df_f["tipo"].value_counts().reset_index()
        tipo_counts.columns = ["tipo", "quantidade"]
        fig_tipo = px.pie(
            tipo_counts, names="tipo", values="quantidade", hole=0.4,
            color_discrete_sequence=["#06b6d4", "#a855f7", "#22c55e", "#f59e0b", "#ef4444", "#475569"],
        )
        fig_tipo.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", height=320,
            legend=dict(font=dict(color="#94a3b8")),
        )
        st.plotly_chart(fig_tipo, use_container_width=True)

    st.markdown("**Linha do tempo dos compromissos**")
    df_timeline = df_f.dropna(subset=["data"]).copy()
    if not df_timeline.empty:
        try:
            df_timeline["inicio_dt"] = pd.to_datetime(
                df_timeline["data"].dt.date.astype(str) + " " + df_timeline["hora_inicio"].astype(str)
            )
            df_timeline["fim_dt"] = pd.to_datetime(
                df_timeline["data"].dt.date.astype(str) + " " + df_timeline["hora_fim"].astype(str)
            )
            fig_gantt = px.timeline(
                df_timeline, x_start="inicio_dt", x_end="fim_dt", y="lider",
                color="tipo", hover_name="titulo",
                color_discrete_sequence=["#06b6d4", "#a855f7", "#22c55e", "#f59e0b", "#ef4444", "#475569"],
            )
            fig_gantt.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                xaxis=dict(gridcolor="#1a2035"), yaxis=dict(gridcolor="#1a2035"),
                height=max(300, 60 * df_timeline["lider"].nunique()),
                legend=dict(font=dict(color="#94a3b8")),
            )
            st.plotly_chart(fig_gantt, use_container_width=True)
        except Exception as e:
            st.info(f"Não foi possível montar a linha do tempo: {e}")
    else:
        st.info("Sem compromissos suficientes para a linha do tempo.")

    st.markdown("---")
    st.markdown("### ✏️ Editar ou excluir compromisso")

    opcoes = {f"{c['id']} — {c['titulo']} ({c['lider']})": c for c in compromissos}
    selecao = st.selectbox("Selecione o compromisso", options=["—"] + list(opcoes.keys()), key="edit_compromisso_select")

    if selecao != "—":
        compromisso = opcoes[selecao]
        with st.form("editar_compromisso"):
            col1, col2 = st.columns(2)
            with col1:
                lider_e = st.text_input("Líder responsável", value=compromisso.get("lider") or "")
                titulo_e = st.text_input("Título / descrição", value=compromisso.get("titulo") or "")
                idx_tipo = TIPOS_COMPROMISSO.index(compromisso["tipo"]) if compromisso.get("tipo") in TIPOS_COMPROMISSO else 0
                tipo_e = st.selectbox("Tipo", TIPOS_COMPROMISSO, index=idx_tipo)
            with col2:
                data_e = st.date_input(
                    "Data",
                    value=date.fromisoformat(str(compromisso["data"])[:10]) if compromisso.get("data") else date.today()
                )
                hora_inicio_e = st.time_input(
                    "Hora de início",
                    value=datetime.strptime(str(compromisso["hora_inicio"]), "%H:%M:%S").time()
                    if compromisso.get("hora_inicio") else time(9, 0)
                )
                hora_fim_e = st.time_input(
                    "Hora de término",
                    value=datetime.strptime(str(compromisso["hora_fim"]), "%H:%M:%S").time()
                    if compromisso.get("hora_fim") else time(10, 0)
                )
                idx_status = STATUS_COMPROMISSO.index(compromisso["status"]) if compromisso.get("status") in STATUS_COMPROMISSO else 0
                status_e = st.selectbox("Status", STATUS_COMPROMISSO, index=idx_status)

            observacoes_e = st.text_area("Observações", value=compromisso.get("observacoes") or "")

            col_save, col_delete = st.columns(2)
            salvar = col_save.form_submit_button("💾 Salvar alterações")
            deletar = col_delete.form_submit_button("🗑️ Excluir compromisso")

            if salvar:
                try:
                    supabase.table("agenda_compromissos").update({
                        "lider": lider_e,
                        "titulo": titulo_e,
                        "tipo": tipo_e,
                        "data": data_e.isoformat(),
                        "hora_inicio": hora_inicio_e.isoformat(),
                        "hora_fim": hora_fim_e.isoformat(),
                        "status": status_e,
                        "observacoes": observacoes_e,
                    }).eq("id", compromisso["id"]).execute()
                    st.success("Compromisso atualizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")

            if deletar:
                try:
                    supabase.table("agenda_compromissos").delete().eq("id", compromisso["id"]).execute()
                    st.success("Compromisso excluído.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")

    st.markdown("---")
    st.markdown(f"**Histórico completo** ({len(df_f)} compromisso(s))")
    colunas_exibir = ["data", "lider", "titulo", "tipo", "hora_inicio", "hora_fim", "horas", "status"]
    colunas_existentes = [c for c in colunas_exibir if c in df_f.columns]
    st.dataframe(df_f[colunas_existentes].sort_values("data", ascending=False), use_container_width=True, hide_index=True)