import streamlit as st

LOGO_URL = "https://twzzolhitqypdosweqnj.supabase.co/storage/v1/object/public/axiom_backend/imagem_email/logo-nav.webp"

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
        </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown(f"""
        <div class="axiom-header">
            <img src="{LOGO_URL}" alt="AXIOM" />
            <div>
                <div class="axiom-badge">Painel Interno</div>
            </div>
        </div>
    """, unsafe_allow_html=True)