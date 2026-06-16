import streamlit as st
from style import apply_axiom_style, render_header, render_footer
from servicos import render_servicos
from emails import render_emails
from leads import render_leads
from conversas import render_conversas
from groq import Groq
from anthropic import Anthropic

st.set_page_config(page_title="AXIOM Painel", page_icon="◆", layout="wide")
apply_axiom_style()

SECRETS_LOGIN = ["PAINEL_SENHA"]
SECRETS_SUPABASE = ["SUPABASE_URL", "SUPABASE_KEY"]


def get_missing_secrets(keys):
    try:
        return [key for key in keys if key not in st.secrets]
    except Exception:
        return list(keys)


def show_secrets_error(missing):
    render_header()
    st.error("Configuração incompleta: secrets não encontrados.")
    st.markdown(
        "Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` "
        "e preencha os valores. No Streamlit Cloud, configure em **Settings → Secrets**."
    )
    st.markdown("Chaves ausentes:")
    for key in missing:
        st.code(key, language="toml")
    st.stop()


def check_password():
    missing = get_missing_secrets(SECRETS_LOGIN)
    if missing:
        show_secrets_error(missing)

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

@st.cache_resource
def get_ai_clients():
    groq = None
    anthropic = None
    try:
        if "GROQ_API_KEY" in st.secrets:
            groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except Exception:
        pass
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    except Exception:
        pass
    return groq, anthropic

groq_client, anthropic_client = get_ai_clients()



@st.cache_resource
def get_supabase():
    missing = get_missing_secrets(SECRETS_SUPABASE)
    if missing:
        show_secrets_error(missing)

    try:
        from supabase import create_client
    except ImportError:
        render_header()
        st.error("Pacote `supabase` não instalado.")
        st.code("pip install -r requirements.txt", language="bash")
        st.stop()

    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


if not check_password():
    st.stop()

supabase = get_supabase()

render_header()

tab_emails, tab_leads, tab_chat, tab_servicos, tab_analytics = st.tabs(
    ["📧 E-mails", "🎯 Leads", "💬 Conversas", "🛠️ Serviços", "📊 Analytics"]
)

with tab_emails:
    render_emails(supabase)

with tab_leads:
    render_leads(supabase)

with tab_chat:
    render_conversas(supabase, groq_client, anthropic_client)

with tab_servicos:
    render_servicos(supabase)

with tab_analytics:
    st.subheader("Análise geral")
    st.info("Em construção — próximo passo")
render_footer()
