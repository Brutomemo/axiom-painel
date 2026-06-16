import streamlit as st
from datetime import date


def calcular_status(data_entrega_2_prevista, data_entrega_2_real, concluido):
    if concluido:
        return "concluído"
    if data_entrega_2_prevista and data_entrega_2_prevista < date.today() and not data_entrega_2_real:
        return "em atraso"
    return "em andamento"


def render_servicos(supabase):
    st.subheader("Acompanhamento de Serviços")

    with st.expander("➕ Novo serviço", expanded=False):
        with st.form("novo_servico", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                empresa = st.text_input("Empresa")
                responsavel = st.text_input("Responsável pela solicitação")
                telefone = st.text_input("Telefone")
                email = st.text_input("E-mail")
                endereco = st.text_input("Endereço da empresa")
                numero_contrato = st.text_input("Número do contrato")

            with col2:
                origem = st.selectbox("Divisão", ["strategic-intelligence", "human-performance"])
                tipo_servico = st.text_input(
                    "Tipo de serviço",
                    placeholder="Ex.: Dashboard, Diagnóstico Psicossocial..."
                )
                data_solicitacao = st.date_input("Data da solicitação", value=date.today())

                label_entrega_1 = (
                    "Data de início do treinamento"
                    if origem == "human-performance"
                    else "Data da 1ª entrega (MVP)"
                )
                label_entrega_2 = (
                    "Data prevista de fim do treinamento"
                    if origem == "human-performance"
                    else "Data prevista da entrega final"
                )

                data_entrega_1 = st.date_input(label_entrega_1, value=None)
                data_entrega_2_prevista = st.date_input(label_entrega_2, value=None)
                data_entrega_2_real = st.date_input(
                    "Data real de conclusão (deixe vazio se ainda não concluído)",
                    value=None
                )

            st.markdown("---")
            col3, col4, col5, col6 = st.columns(4)
            with col3:
                preco_cobrado = st.number_input("Preço cobrado (R$)", min_value=0.0, step=100.0)
            with col4:
                custos_projeto = st.number_input("Custos do projeto (R$)", min_value=0.0, step=100.0)
            with col5:
                mensalidade = st.number_input("Mensalidade (R$, se houver)", min_value=0.0, step=50.0)
            with col6:
                concluido = st.checkbox("Concluído")

            observacoes = st.text_area("Observações")

            submitted = st.form_submit_button("Salvar serviço")

            if submitted:
                lucro = preco_cobrado - custos_projeto
                status = calcular_status(data_entrega_2_prevista, data_entrega_2_real, concluido)

                try:
                    supabase.table("servicos_prestados").insert({
                        "empresa": empresa,
                        "responsavel": responsavel,
                        "telefone": telefone,
                        "email": email,
                        "endereco": endereco,
                        "tipo_servico": tipo_servico,
                        "origem": origem,
                        "numero_contrato": numero_contrato,
                        "data_solicitacao": data_solicitacao.isoformat() if data_solicitacao else None,
                        "data_entrega_1": data_entrega_1.isoformat() if data_entrega_1 else None,
                        "data_entrega_2_prevista": data_entrega_2_prevista.isoformat() if data_entrega_2_prevista else None,
                        "data_entrega_2_real": data_entrega_2_real.isoformat() if data_entrega_2_real else None,
                        "preco_cobrado": preco_cobrado,
                        "custos_projeto": custos_projeto,
                        "lucro": lucro,
                        "mensalidade": mensalidade,
                        "concluido": concluido,
                        "status": status,
                        "observacoes": observacoes,
                    }).execute()
                    st.success("Serviço registrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

                    

    st.markdown("---")

    try:
        result = supabase.table("servicos_prestados").select("*").order("created_at", desc=True).execute()
        servicos = result.data
    except Exception as e:
        st.error(f"Erro ao carregar serviços: {e}")
        servicos = []

    if not servicos:
        st.info("Nenhum serviço registrado ainda.")
        return

    col_a, col_b, col_c = st.columns(3)
    total_servicos = len(servicos)
    em_atraso = sum(1 for s in servicos if s.get("status") == "em atraso")
    lucro_total = sum(s.get("lucro") or 0 for s in servicos)

    col_a.metric("Total de serviços", total_servicos)
    col_b.metric("Em atraso", em_atraso)
    col_c.metric("Lucro total (R$)", f"{lucro_total:,.2f}")

    import pandas as pd
    df = pd.DataFrame(servicos)
    colunas_exibir = [
        "empresa", "responsavel", "tipo_servico", "origem",
        "status", "preco_cobrado", "lucro", "mensalidade", "numero_contrato"
    ]
    st.dataframe(df[colunas_exibir], use_container_width=True)

    st.markdown("---")
    st.subheader("✏️ Editar serviço existente")

    opcoes = {f"{s['id']} — {s['empresa']} ({s['tipo_servico']})": s for s in servicos}
    selecao = st.selectbox("Selecione o serviço para editar", options=["—"] + list(opcoes.keys()))

    if selecao != "—":
        servico = opcoes[selecao]

        with st.form("editar_servico"):
            col1, col2 = st.columns(2)

            with col1:
                empresa_e = st.text_input("Empresa", value=servico.get("empresa") or "")
                responsavel_e = st.text_input("Responsável", value=servico.get("responsavel") or "")
                telefone_e = st.text_input("Telefone", value=servico.get("telefone") or "")
                email_e = st.text_input("E-mail", value=servico.get("email") or "")
                endereco_e = st.text_input("Endereço", value=servico.get("endereco") or "")
                numero_contrato_e = st.text_input("Número do contrato", value=servico.get("numero_contrato") or "")

            with col2:
                origem_e = st.selectbox(
                    "Divisão", ["strategic-intelligence", "human-performance"],
                    index=0 if servico.get("origem") == "strategic-intelligence" else 1
                )
                tipo_servico_e = st.text_input("Tipo de serviço", value=servico.get("tipo_servico") or "")

                def parse_date(value):
                    if not value:
                        return None
                    return date.fromisoformat(value) if isinstance(value, str) else value

                data_solicitacao_e = st.date_input(
                    "Data da solicitação", value=parse_date(servico.get("data_solicitacao"))
                )
                data_entrega_1_e = st.date_input(
                    "Data entrega 1 / início treinamento", value=parse_date(servico.get("data_entrega_1"))
                )
                data_entrega_2_prevista_e = st.date_input(
                    "Data prevista entrega 2 / fim treinamento",
                    value=parse_date(servico.get("data_entrega_2_prevista"))
                )
                data_entrega_2_real_e = st.date_input(
                    "Data real de conclusão", value=parse_date(servico.get("data_entrega_2_real"))
                )

            st.markdown("---")
            col3, col4, col5, col6 = st.columns(4)
            with col3:
                preco_cobrado_e = st.number_input(
                    "Preço cobrado (R$)", min_value=0.0, step=100.0,
                    value=float(servico.get("preco_cobrado") or 0)
                )
            with col4:
                custos_projeto_e = st.number_input(
                    "Custos do projeto (R$)", min_value=0.0, step=100.0,
                    value=float(servico.get("custos_projeto") or 0)
                )
            with col5:
                mensalidade_e = st.number_input(
                    "Mensalidade (R$)", min_value=0.0, step=50.0,
                    value=float(servico.get("mensalidade") or 0)
                )
            with col6:
                concluido_e = st.checkbox("Concluído", value=servico.get("concluido") or False)

            observacoes_e = st.text_area("Observações", value=servico.get("observacoes") or "")

            col_save, col_delete = st.columns(2)
            salvar = col_save.form_submit_button("💾 Salvar alterações")
            deletar = col_delete.form_submit_button("🗑️ Excluir serviço")

            if salvar:
                lucro_e = preco_cobrado_e - custos_projeto_e
                status_e = calcular_status(data_entrega_2_prevista_e, data_entrega_2_real_e, concluido_e)

                try:
                    supabase.table("servicos_prestados").update({
                        "empresa": empresa_e,
                        "responsavel": responsavel_e,
                        "telefone": telefone_e,
                        "email": email_e,
                        "endereco": endereco_e,
                        "tipo_servico": tipo_servico_e,
                        "origem": origem_e,
                        "numero_contrato": numero_contrato_e,
                        "data_solicitacao": data_solicitacao_e.isoformat() if data_solicitacao_e else None,
                        "data_entrega_1": data_entrega_1_e.isoformat() if data_entrega_1_e else None,
                        "data_entrega_2_prevista": data_entrega_2_prevista_e.isoformat() if data_entrega_2_prevista_e else None,
                        "data_entrega_2_real": data_entrega_2_real_e.isoformat() if data_entrega_2_real_e else None,
                        "preco_cobrado": preco_cobrado_e,
                        "custos_projeto": custos_projeto_e,
                        "lucro": lucro_e,
                        "mensalidade": mensalidade_e,
                        "concluido": concluido_e,
                        "status": status_e,
                        "observacoes": observacoes_e,
                    }).eq("id", servico["id"]).execute()
                    st.success("Serviço atualizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")

            if deletar:
                try:
                    supabase.table("servicos_prestados").delete().eq("id", servico["id"]).execute()
                    st.success("Serviço excluído.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")