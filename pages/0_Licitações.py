import streamlit as st
from src.dify_client import DifyClient
import os
import tempfile

# Initialize Dify client
dify_client = DifyClient()

# Page config
st.set_page_config(page_title="Licitações - Licita.AI", page_icon="📄", layout="wide")

# Title
st.title("📄 Licitações")

# Initialize session state for form data
if "cliente" not in st.session_state:
    st.session_state.cliente = ""
if "referencia" not in st.session_state:
    st.session_state.referencia = ""
if "id_licitacao" not in st.session_state:
    st.session_state.id_licitacao = ""
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None

# Form for new tender
with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        cliente = st.text_input("Cliente", key="cliente")
    with col2:
        referencia = st.text_input("Referência", key="referencia")
    with col3:
        id_licitacao = st.text_input("ID", key="id")

    uploaded_files = st.file_uploader(
        "Documentos da Licitação (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        key="docs",
    )

# Submit button outside the form
if uploaded_files:
    submit_disabled = not (cliente and referencia and id_licitacao)
    if st.button("Nova Licitação", type="primary", disabled=submit_disabled):
        dataset_name = f"{cliente} - {referencia} - {id_licitacao}"

        with st.spinner("Criando base de conhecimento..."):
            try:
                # Create dataset
                dataset_id = dify_client.create_dataset(name=dataset_name)

                # Upload files
                for uploaded_file in uploaded_files:
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp_file:
                        # Write the uploaded file to the temporary file
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file.flush()

                        # Upload to Dify
                        with open(tmp_file.name, "rb") as f:
                            dify_client.upload_knowledge_file(
                                f.read(), uploaded_file.name, dataset_id=dataset_id
                            )

                        # Clean up the temporary file
                        os.unlink(tmp_file.name)

                st.success("Base de conhecimento criada com sucesso!")
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao criar base de conhecimento: {str(e)}")
else:
    st.info("⬆️ Faça upload dos documentos da licitação para continuar")

# List of existing datasets
st.subheader("Bases de Conhecimento")

with st.container():
    try:
        # Fetch all datasets
        datasets = dify_client.fetch_all_datasets()

        if not datasets:
            st.info("Nenhuma base de conhecimento encontrada")
        else:
            for dataset in datasets:
                with st.expander(f"📁 {dataset['name']}", expanded=False):
                    st.caption(dataset.get("description", "Sem descrição"))
                    st.divider()

                    # List files in dataset
                    files = dify_client.list_dataset_files(dataset["id"])

                    if not files:
                        st.info("Nenhum arquivo encontrado")
                    else:
                        for file in files:
                            st.text(f"📄 {file['name']}")

    except Exception as e:
        st.error(f"Erro ao carregar bases de conhecimento: {str(e)}")
