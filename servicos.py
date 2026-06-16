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