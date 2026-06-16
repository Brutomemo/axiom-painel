import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter

STOPWORDS_PT = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "em", "na", "no",
    "nas", "nos", "para", "por", "com", "sem", "um", "uma", "uns", "umas",
    "e", "ou", "que", "se", "é", "são", "foi", "ser", "estar", "está",
    "como", "mais", "mas", "muito", "já", "não", "sim", "isso", "isto",
    "essa", "esse", "esta", "este", "qual", "quais", "quando", "onde",
    "porque", "também", "ainda", "só", "tem", "ter", "vai", "vou",
    "minha", "meu", "minhas", "meus", "sua", "seu", "suas", "seus",
    "nossa", "nosso", "ao", "aos", "à", "às", "pelo", "pela", "pelos",
    "pelas", "num", "numa", "eu", "você", "voce", "ele", "ela", "nós",
    "preciso", "gostaria", "obrigado", "obrigada", "olá", "ola", "bom",
    "dia", "tarde", "noite",
}


def limpar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-zà-ú\s]", " ", texto)
    palavras = texto.split()
    return [p for p in palavras if p not in STOPWORDS_PT and len(p) > 2]


def render_conversas(supabase, groq_client=None, anthropic_client=None):
    st.subheader("Histórico de Conversas")

    try:
        result = supabase.table("chat_history").select("*").order("created_at", desc=True).execute()
        conversas = result.data
    except Exception as e:
        st.error(f"Erro ao carregar conversas: {e}")
        conversas = []

    if not conversas:
        st.info("Nenhuma conversa registrada ainda.")
        return

    df = pd.DataFrame(conversas)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total de mensagens", len(df))
    col_b.metric("Sessões únicas", df["session_id"].nunique())
    col_c.metric("Vinculadas a leads", df["lead_id"].notna().sum())

    st.markdown("---")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_origem = st.selectbox(
            "Filtrar por divisão", ["Todas", "strategic-intelligence", "human-performance"]
        )
    with col_f2:
        filtro_modelo = st.selectbox("Filtrar por modelo", ["Todos"] + df["model"].dropna().unique().tolist())

    df_filtrado = df.copy()
    if filtro_origem != "Todas":
        df_filtrado = df_filtrado[df_filtrado["origem"] == filtro_origem]
    if filtro_modelo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["model"] == filtro_modelo]

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Mensagens por modelo de IA**")
        modelo_counts = df_filtrado["model"].value_counts().reset_index()
        modelo_counts.columns = ["modelo", "quantidade"]
        fig_modelo = px.bar(
            modelo_counts, x="modelo", y="quantidade",
            color_discrete_sequence=["#06b6d4"],
        )
        fig_modelo.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            xaxis=dict(gridcolor="#1a2035"), yaxis=dict(gridcolor="#1a2035"),
            height=320,
        )
        st.plotly_chart(fig_modelo, use_container_width=True)

    with col_g2:
        st.markdown("**Top palavras-chave (perguntas dos clientes)**")
        todas_palavras = []
        for msg in df_filtrado["user_message"].dropna():
            todas_palavras.extend(limpar_texto(msg))

        if todas_palavras:
            contagem = Counter(todas_palavras).most_common(15)
            top_df = pd.DataFrame(contagem, columns=["palavra", "frequência"])
            fig_palavras = px.bar(
                top_df.sort_values("frequência"), x="frequência", y="palavra",
                orientation="h",
                color_discrete_sequence=["#a855f7"],
            )
            fig_palavras.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                xaxis=dict(gridcolor="#1a2035"), yaxis=dict(gridcolor="#1a2035"),
                height=max(320, 24 * len(top_df)),
            )
            st.plotly_chart(fig_palavras, use_container_width=True)
        else:
            st.info("Sem dados suficientes para análise de palavras.")

    st.markdown("---")

    st.markdown("### 🤖 Resumo temático com IA")
    st.caption(
        "Gera um resumo das conversas filtradas, identificando temas recorrentes, "
        "dúvidas frequentes e oportunidades — como os resumos de avaliações em e-commerces."
    )

    col_ia1, col_ia2 = st.columns([3, 1])
    with col_ia1:
        forcar_modelo = st.radio(
            "Modelo", ["Automático (por volume)", "Forçar Groq", "Forçar Claude"],
            horizontal=True
        )
    with col_ia2:
        gerar = st.button("✨ Gerar resumo", use_container_width=True)

    if gerar:
        mensagens_texto = "\n".join(
            f"- {msg}" for msg in df_filtrado["user_message"].dropna().tolist()
        )

        if not mensagens_texto:
            st.warning("Nenhuma mensagem disponível para resumir com esses filtros.")
        else:
            num_palavras = len(mensagens_texto.split())

            if forcar_modelo == "Forçar Claude":
                usar_claude = True
            elif forcar_modelo == "Forçar Groq":
                usar_claude = False
            else:
                usar_claude = num_palavras > 1500

            prompt = (
                "Você é um analista de atendimento ao cliente. Abaixo estão mensagens reais "
                "enviadas por clientes em um chat comercial. Gere um resumo executivo, em "
                "português, no estilo de resumos de avaliações de e-commerce, identificando: "
                "(1) principais temas e dúvidas recorrentes, (2) sentimento geral predominante, "
                "(3) oportunidades de negócio percebidas. Seja conciso, objetivo e use bullet points.\n\n"
                f"Mensagens:\n{mensagens_texto}"
            )

            with st.spinner(f"Gerando resumo via {'Claude' if usar_claude else 'Groq'}..."):
                try:
                    if usar_claude and anthropic_client:
                        resposta = anthropic_client.messages.create(
                            model="claude-3-5-haiku-20241022",
                            max_tokens=1024,
                            messages=[{"role": "user", "content": prompt}],
                        )
                        texto_resumo = resposta.content[0].text
                    elif groq_client:
                        resposta = groq_client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        texto_resumo = resposta.choices[0].message.content
                    else:
                        texto_resumo = "Clientes de IA não configurados."

                    st.markdown(
                        f'<div style="background:#0d0f18;border:1px solid #1a2035;'
                        f'border-left:3px solid #06b6d4;border-radius:0 8px 8px 0;'
                        f'padding:20px;color:#e2e8f0;">{texto_resumo}</div>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar resumo: {e}")

    st.markdown("---")
    st.markdown(f"**Histórico detalhado** ({len(df_filtrado)} mensagem(ns))")
    colunas_exibir = ["created_at", "session_id", "user_message", "assistant_message", "model", "origem", "lead_id"]
    colunas_existentes = [c for c in colunas_exibir if c in df_filtrado.columns]
    st.dataframe(
        df_filtrado[colunas_existentes].sort_values("created_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )