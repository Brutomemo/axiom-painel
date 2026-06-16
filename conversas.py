import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter
import tempfile
from itertools import combinations
from pyvis.network import Network
import networkx as nx

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

def gerar_grafo_palavras(textos, max_palavras=30):
    co_ocorrencia = Counter()
    frequencia = Counter()

    for texto in textos:
        palavras = list(set(limpar_texto(texto)))
        frequencia.update(palavras)
        for par in combinations(sorted(palavras), 2):
            co_ocorrencia[par] += 1

    top_palavras = {p for p, _ in frequencia.most_common(max_palavras)}
    if not top_palavras:
        return None

    G = nx.Graph()
    for palavra in top_palavras:
        G.add_node(palavra, size=frequencia[palavra])

    for (p1, p2), peso in co_ocorrencia.items():
        if p1 in top_palavras and p2 in top_palavras and peso > 0:
            G.add_edge(p1, p2, weight=peso)

    if G.number_of_nodes() == 0:
        return None

    net = Network(
        height="420px", width="100%",
        bgcolor="#07080d", font_color="#e2e8f0",
        notebook=False,
    )

    max_freq = max(frequencia[p] for p in top_palavras)

    for palavra in top_palavras:
        freq = frequencia[palavra]
        tamanho = 14 + (freq / max_freq) * 36
        intensidade = freq / max_freq
        cor = f"rgba(6,182,212,{0.4 + intensidade * 0.6})" if intensidade > 0.5 else f"rgba(168,85,247,{0.4 + intensidade * 0.6})"
        net.add_node(
            palavra, label=palavra, size=tamanho,
            color=cor, font={"color": "#e2e8f0", "size": 16},
        )

    for (p1, p2), peso in co_ocorrencia.items():
        if p1 in top_palavras and p2 in top_palavras:
            net.add_edge(p1, p2, value=peso, color="rgba(148,163,184,0.25)")

    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {"gravitationalConstant": -50, "springLength": 100},
        "solver": "forceAtlas2Based",
        "stabilization": {"iterations": 150}
      },
      "interaction": {"hover": true}
    }
    """)

    return net
    
    
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
        st.markdown("**Rede de palavras-chave (conversas filtradas)**")
        st.caption("Tamanho = frequência · Conexões = co-ocorrência na mesma mensagem")

        textos_validos = df_filtrado["user_message"].dropna().tolist()

        if textos_validos:
            net = gerar_grafo_palavras(textos_validos)
            if net is None:
                st.info("Sem dados suficientes para gerar o grafo.")
            else:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
                    temp_file = f.name
                net.write_html(temp_file, notebook=False)
                with open(temp_file, "r", encoding="utf-8") as f:
                    html_content = f.read()

                html_content = html_content.replace(
                    "<style type=\"text/css\">",
                    """<style type="text/css">
                    html, body {
                        margin: 0;
                        padding: 0;
                        background: #07080d !important;
                    }
                    #mynetwork {
                        background: #07080d !important;
                        border: 1px solid #1a2035;
                        border-radius: 12px;
                    }
                    """
                )
                st.components.v1.html(html_content, height=440, scrolling=False)
        else:
            st.info("Sem dados suficientes para análise.")

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