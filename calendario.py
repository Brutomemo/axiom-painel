import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar

CORES_TIPO = {
    "Reunião": "#06b6d4",
    "Atendimento a Cliente": "#a855f7",
    "Desenvolvimento": "#22c55e",
    "Diagnóstico/Treinamento": "#f59e0b",
    "Administrativo": "#475569",
    "Outro": "#ef4444",
}

CUSTOM_CSS = """
    .fc {
        background-color: #07080d;
        color: #e2e8f0;
    }
    .fc .fc-toolbar-title {
        color: #f1f5f9;
        font-size: 18px;
    }
    .fc .fc-button {
        background-color: #0d0f18;
        border: 1px solid #1a2035;
        color: #94a3b8;
        box-shadow: none;
    }
    .fc .fc-button:hover {
        background-color: rgba(6,182,212,0.1);
        border-color: #06b6d4;
        color: #06b6d4;
    }
    .fc .fc-button-active {
        background-color: rgba(6,182,212,0.15) !important;
        border-color: #06b6d4 !important;
        color: #06b6d4 !important;
    }
    .fc-theme-standard td, .fc-theme-standard th {
        border-color: #1a2035;
    }
    .fc .fc-daygrid-day.fc-day-today,
    .fc .fc-timegrid-col.fc-day-today {
        background-color: rgba(6,182,212,0.06);
    }
    .fc-col-header-cell-cushion, .fc-daygrid-day-number {
        color: #94a3b8;
    }
"""


def render_calendario(supabase):
    st.subheader("Calendário")
    st.caption("Visualização mensal, semanal e diária dos compromissos registrados na agenda.")

    try:
        result = supabase.table("agenda_compromissos").select("*").execute()
        compromissos = result.data
    except Exception as e:
        st.error(f"Erro ao carregar compromissos: {e}")
        compromissos = []

    if not compromissos:
        st.info("Nenhum compromisso registrado ainda. Cadastre na sub-aba 'Lista e Métricas'.")
        return

    lideres = sorted({c.get("lider") for c in compromissos if c.get("lider")})
    filtro_lider = st.selectbox("Filtrar por líder", ["Todos"] + lideres, key="calendario_filtro_lider")

    eventos = []
    for c in compromissos:
        if filtro_lider != "Todos" and c.get("lider") != filtro_lider:
            continue

        data_inicio = c.get("data")
        data_fim = c.get("data_fim") or data_inicio
        cor = CORES_TIPO.get(c.get("tipo"), "#06b6d4")
        titulo_evento = f"{c.get('titulo')} — {c.get('lider')}"

        if data_inicio != data_fim:
            try:
                data_fim_exclusiva = (
                    datetime.fromisoformat(str(data_fim)) + timedelta(days=1)
                ).date().isoformat()
            except Exception:
                data_fim_exclusiva = data_fim
            eventos.append({
                "id": str(c["id"]),
                "title": titulo_evento,
                "start": str(data_inicio),
                "end": data_fim_exclusiva,
                "allDay": True,
                "backgroundColor": cor,
                "borderColor": cor,
            })
        else:
            eventos.append({
                "id": str(c["id"]),
                "title": titulo_evento,
                "start": f"{data_inicio}T{c.get('hora_inicio')}",
                "end": f"{data_fim}T{c.get('hora_fim')}",
                "backgroundColor": cor,
                "borderColor": cor,
            })

    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "initialView": "dayGridMonth",
        "locale": "pt-br",
        "buttonText": {
            "today": "Hoje", "month": "Mês", "week": "Semana", "day": "Dia",
        },
        "height": "auto",
        "slotMinTime": "06:00:00",
        "slotMaxTime": "22:00:00",
    }

    resultado = calendar(
        events=eventos,
        options=calendar_options,
        custom_css=CUSTOM_CSS,
        key="axiom_calendar",
    )

    if resultado.get("callback") == "eventClick":
        evento = resultado["eventClick"]["event"]
        try:
            compromisso_id = int(evento["id"])
        except (TypeError, ValueError):
            compromisso_id = None

        detalhe = next((c for c in compromissos if c["id"] == compromisso_id), None)
        if detalhe:
            st.markdown("---")
            st.markdown(f"**{detalhe.get('titulo')}**")
            col1, col2, col3 = st.columns(3)
            col1.write(f"Líder: {detalhe.get('lider')}")
            col2.write(f"Tipo: {detalhe.get('tipo')}")
            col3.write(f"Status: {detalhe.get('status')}")
            st.write(f"Horário: {detalhe.get('hora_inicio')} às {detalhe.get('hora_fim')}")
            if detalhe.get("observacoes"):
                st.caption(detalhe["observacoes"])