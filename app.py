import streamlit as st
from supabase import create_client
from style import apply_axiom_style, render_header

st.set_page_config(page_title="AXIOM Painel", page_icon="◆", layout="wide")
apply_axiom_style()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["PAINEL_SENHA"]:
            st.session_state["autenticado"] = True
            del st.session_state["password"]
        else:
            st.session_state["autenticado"] = False

    if "autenticado" not in st.session_state:
        render_header()
        st.text_input("Senha", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["autenticado"]:
        render_header()
        st.text_input("Senha", type="password", on_change=password_entered, key="password")
        st.error("Senha incorreta")
        return False
    else:
        return True

if not check_password():
    st.stop()

render_header()

tab_emails, tab_leads, tab_chat, tab_analytics = st.tabs(
    ["📧 E-mails", "🎯 Leads", "💬 Conversas", "📊 Analytics"]
)

with tab_emails:
    st.subheader("E-mails recebidos")
    st.info("Em construção — próximo passo")

with tab_leads:
    st.subheader("Leads")
    st.info("Em construção — próximo passo")

with tab_chat:
    st.subheader("Histórico de conversas")
    st.info("Em construção — próximo passo")

with tab_analytics:
    st.subheader("Análise geral")
    st.info("Em construção — próximo passo")