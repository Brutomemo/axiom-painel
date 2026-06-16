import streamlit as st
import resend
from datetime import datetime, timezone


def render_emails(supabase):
    st.subheader("E-mails Recebidos")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_status = st.selectbox("Status", ["Todos", "novo", "lido", "respondido"])
    with col_f2:
        ordenacao = st.selectbox("Ordenar por", ["Mais recentes", "Mais antigos"])

    try:
        query = supabase.table("emails_recebidos").select("*")
        if filtro_status != "Todos":
            query = query.eq("status", filtro_status)
        query = query.order("created_at", desc=(ordenacao == "Mais recentes"))
        result = query.execute()
        emails = result.data
    except Exception as e:
        st.error(f"Erro ao carregar e-mails: {e}")
        emails = []

    col_a, col_b, col_c = st.columns(3)
    try:
        total = supabase.table("emails_recebidos").select("id", count="exact").execute()
        novos = supabase.table("emails_recebidos").select("id", count="exact").eq("status", "novo").execute()
        respondidos = supabase.table("emails_recebidos").select("id", count="exact").eq("status", "respondido").execute()
        col_a.metric("Total recebidos", total.count or 0)
        col_b.metric("Novos", novos.count or 0)
        col_c.metric("Respondidos", respondidos.count or 0)
    except Exception:
        pass

    st.markdown("---")

    if not emails:
        st.info("Nenhum e-mail encontrado com esse filtro.")
        return

    for email in emails:
        status = email.get("status", "novo")
        badge_color = {"novo": "🔵", "lido": "🟡", "respondido": "🟢"}.get(status, "⚪")

        with st.expander(
            f"{badge_color} **{email.get('nome_remetente') or email.get('de')}** "
            f"— {email.get('assunto') or '(sem assunto)'}"
        ):
            col_info, col_lead = st.columns([2, 1])
            with col_info:
                st.markdown(f"**De:** {email.get('de')}")
                st.markdown(f"**Recebido em:** {email.get('created_at', '')[:16]}")
            with col_lead:
                if email.get("lead_id"):
                    st.success(f"Lead vinculado: #{email['lead_id']}")
                else:
                    st.warning("Sem lead vinculado")

            st.markdown("**Mensagem:**")
            corpo_html = email.get("corpo_html")
            corpo_texto = email.get("corpo_texto")
            if corpo_html:
                st.markdown(
                    f'<div style="background:#0d0f18;border:1px solid #1a2035;'
                    f'border-radius:8px;padding:16px;color:#94a3b8;">{corpo_html}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.text(corpo_texto or "(sem conteúdo)")

            if status == "novo":
                if st.button("Marcar como lido", key=f"lido_{email['id']}"):
                    supabase.table("emails_recebidos").update({"status": "lido"}).eq("id", email["id"]).execute()
                    st.rerun()

            st.markdown("**Responder:**")
            resposta_texto = email.get("resposta_enviada") or ""
            nova_resposta = st.text_area(
                "Sua resposta",
                value=resposta_texto,
                key=f"resposta_{email['id']}",
                height=150,
                disabled=(status == "respondido")
            )

            if status != "respondido":
                if st.button("Enviar resposta", key=f"enviar_{email['id']}"):
                    if not nova_resposta.strip():
                        st.warning("Escreva uma resposta antes de enviar.")
                    else:
                        try:
                            resend.api_key = st.secrets["RESEND_API_KEY"]
                            resend.Emails.send({
                                "from": "AXIOM <contato@axiomstrategic.com.br>",
                                "to": [email["de"]],
                                "subject": f"Re: {email.get('assunto') or 'Contato AXIOM'}",
                                "text": nova_resposta,
                            })
                            supabase.table("emails_recebidos").update({
                                "status": "respondido",
                                "respondido_em": datetime.now(timezone.utc).isoformat(),
                                "resposta_enviada": nova_resposta,
                            }).eq("id", email["id"]).execute()
                            st.success("Resposta enviada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao enviar resposta: {e}")
            else:
                st.caption(f"Respondido em {email.get('respondido_em', '')[:16]}")