import streamlit as st
from datetime import datetime, timedelta

try:
    from streamlit_calendar import calendar
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

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
        background-color: #07080d !important;
        color: #e2e8f0;
    }
    .fc .fc-toolbar-title {
        color: #f1f5f9;
        font-size: 18px;
    }
    .fc .fc-button {
        background-color: #0d0f18 !important;
        border: 1px solid #1a2035 !important;
        color: #94a3b8 !important;
        box-shadow: none !important;
    }
    .fc .fc-button:hover {
        background-color: rgba(6,182,212,0.1) !important;
        border-color: #06b6d4 !important;
        color: #06b6d4 !important;
    }
    .fc .fc-button-primary:not(:disabled).fc-button-active {
        background-color: rgba(6,182,212,0.15) !important;
        border-color: #06b6d4 !important;
        color: #06b6d4 !important;
    }
    .fc-theme-standard td, .fc-theme-standard th {
        border-color: #1a2035 !important;
    }
    .fc .fc-daygrid-day.fc-day-today,
    .fc .fc-timegrid-col.fc-day-today {
        background-color: rgba(6,182,212,0.06) !important;
    }
    .fc-col-header-cell-cushion, .fc-daygrid-day-number {
        color: #94a3b8 !important;
    }
    .fc-daygrid-day-frame {
        background-color: #07080d;
    }
    .fc-scrollgrid {
        border-color: #1a2035 !important;
    }
"""


def render_calendario(supabase):
    st.subheader("Calendário")
    st.caption("Visualização mensal, semanal e diária dos compromissos registrados na agenda.")

    if not CALENDAR_AVAILABLE:
        st.error("Biblioteca `streamlit-calendar` não encontrada. Verifique o requirements.txt e reinicie o app.")
        st.code("streamlit-calendar", language="text")
        return

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
    filtro_lider = st.selectbox(
        "Filtrar por líder", ["Todos"] + lideres, key="calendario_filtro_lider"
    )

    eventos = []
    for c in compromissos:
        if filtro_lider != "Todos" and c.get("lider") != filtro_lider:
            continue

        data_inicio = c.get("data")
        data_fim = c.get("data_fim") or data_inicio
        cor = CORES_TIPO.get(c.get("tipo"), "#06b6d4")
        titulo_evento = f"{c.get('titulo', '')} — {c.get('lider', '')}"

        hora_inicio = c.get("hora_inicio") or "00:00:00"
        hora_fim = c.get("hora_fim") or "01:00:00"

        if str(data_inicio)[:10] != str(data_fim)[:10]:
            try:
                data_fim_exclusiva = (
                    datetime.fromisoformat(str(data_fim)[:10]) + timedelta(days=1)
                ).date().isoformat()
            except Exception:
                data_fim_exclusiva = str(data_fim)[:10]
            eventos.append({
                "id": str(c["id"]),
                "title": titulo_evento,
                "start": str(data_inicio)[:10],
                "end": data_fim_exclusiva,
                "allDay": True,
                "backgroundColor": cor,
                "borderColor": cor,
                "textColor": "#ffffff",
            })
        else:
            eventos.append({
                "id": str(c["id"]),
                "title": titulo_evento,
                "start": f"{str(data_inicio)[:10]}T{str(hora_inicio)[:5]}",
                "end": f"{str(data_fim)[:10]}T{str(hora_fim)[:5]}",
                "backgroundColor": cor,
                "borderColor": cor,
                "textColor": "#ffffff",
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
            "today": "Hoje",
            "month": "Mês",
            "week": "Semana",
            "day": "Dia",
        },
        "height": 650,
        "slotMinTime": "06:00:00",
        "slotMaxTime": "22:00:00",
        "expandRows": True,
        "nowIndicator": True,
    }

    resultado = calendar(
        events=eventos,
        options=calendar_options,
        custom_css=CUSTOM_CSS,
        key="axiom_calendar",
    )

    if resultado and resultado.get("callback") == "eventClick":
        evento_clicado = resultado["eventClick"]["event"]
        try:
            compromisso_id = int(evento_clicado.get("id", 0))
        except (TypeError, ValueError):
            compromisso_id = None

        if compromisso_id:
            detalhe = next((c for c in compromissos if c["id"] == compromisso_id), None)
            if detalhe:
                st.markdown("---")
                st.markdown(
                    f'<div style="background:#0d0f18;border:1px solid #1a2035;'
                    f'border-left:3px solid #06b6d4;border-radius:0 8px 8px 0;padding:16px 20px;">'
                    f'<strong style="color:#f1f5f9;font-size:15px;">{detalhe.get("titulo")}</strong>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                col1, col2, col3 = st.columns(3)
                col1.metric("Líder", detalhe.get("lider") or "—")
                col2.metric("Tipo", detalhe.get("tipo") or "—")
                col3.metric("Status", detalhe.get("status") or "—")
                st.write(
                    f"⏱️ {str(detalhe.get('hora_inicio', ''))[:5]} "
                    f"→ {str(detalhe.get('hora_fim', ''))[:5]}"
                )
                if detalhe.get("observacoes"):
                    st.caption(detalhe["observacoes"])
