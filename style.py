import streamlit as st

LOGO_URL = "https://twzzolhitqypdosweqnj.supabase.co/storage/v1/object/public/axiom_backend/imagem_email/logo-email.png"

ORIGEM_COLORS = {
    "strategic-intelligence": "#d47406",
    "human-performance": "#11c5fc",
}


def style_chart(fig, height=320, legend=True, grid_axes=False):
    layout = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font_color": "#94a3b8",
        "height": height,
        "margin": dict(t=20, b=20, l=20, r=20),
    }
    if legend:
        layout["legend"] = dict(font=dict(color="#94a3b8"))
    if grid_axes:
        layout["xaxis"] = dict(gridcolor="#1a2035")
        layout["yaxis"] = dict(gridcolor="#1a2035")
    fig.update_layout(**layout)
    return fig

def apply_axiom_style():
    st.markdown("""
        <style>
        .stApp {
            background-color: #07080d;
        }
        section[data-testid="stSidebar"] {
            background-color: #0d0f18;
            border-right: 1px solid #1a2035;
        }
        h1, h2, h3 {
            color: #f1f5f9 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #0d0f18;
            border-radius: 8px;
            border: 1px solid #1a2035;
            color: #94a3b8;
            padding: 8px 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(6,182,212,0.1) !important;
            border-color: #06b6d4 !important;
            color: #06b6d4 !important;
        }
        div[data-testid="stMetric"] {
            background-color: #0d0f18;
            border: 1px solid #1a2035;
            border-radius: 12px;
            padding: 16px;
        }
        div[data-testid="stMetricValue"] {
            color: #06b6d4 !important;
        }
        .axiom-header {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px 0 24px;
            border-bottom: 1px solid #1a2035;
            margin-bottom: 24px;
        }
        .axiom-header img {
            height: 48px;
        }
        .axiom-badge {
            background: rgba(6,182,212,0.08);
            border: 1px solid rgba(6,182,212,0.2);
            border-radius: 20px;
            padding: 4px 16px;
            color: #06b6d4;
            font-size: 11px;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-weight: 600;
        }
        div[data-testid="stPlotlyChart"] {
            background-color: transparent;
        }
        div[data-testid="stPlotlyChart"] .js-plotly-plot .plotly .legend {
            font-size: 12px;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown(f"""
        <div class="axiom-header">
            <img src="{LOGO_URL}" alt="AXIOM" />
            <div style="display: flex; align-items: center; gap: 16px;">
                <div class="axiom-badge">Painel Interno</div>
                <div style="border-left: 1px solid #1a2035; padding-left: 16px;">
                    <p style="
                        color: #94A3B8;
                        font-size: 11px;
                        font-style: italic;
                        margin: 0;
                        direction: rtl;
                    ">
                        בָּרוּךְ אַתָּה ה' אֱ-לֹהֵינוּ מֶלֶךְ הָעוֹלָם
                    </p>
                    <p style="
                        color: #94A3B8;
                        font-size: 10px;
                        margin: 2px 0 0;
                    ">
                        Baruch Atá Adonai Eloheinu Melech HaOlam
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown("""
        <div style="
            margin-top: 48px;
            padding: 24px 0;
            border-top: 1px solid #1a2035;
            text-align: center;
        ">
            <p style="
                color: #94A3B8;
                font-size: 12px;
                font-style: italic;
                margin: 0 0 8px;
                direction: rtl;
            ">
                שיהיה שלום, אושר והצלחה בכל החלטה ובכל לקוח שייכנס למקום הזה
            </p>
            <p style="
                color: #334155;
                font-size: 11px;
                margin: 0 0 16px;
            ">
                Que haja paz, felicidade e sucesso em cada decisão e em cada cliente que entrar neste lugar
            </p>
            <p style="
                color: #334155;
                font-size: 11px;
                letter-spacing: 1px;
                text-transform: uppercase;
                margin: 0;
            ">
                AXIOM 2026 · Desenvolvido por AXIOM Strategic Intelligence · Todos os direitos reservados
            </p>
        </div>
    """, unsafe_allow_html=True)