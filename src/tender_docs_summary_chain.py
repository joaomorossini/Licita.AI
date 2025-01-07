import os
import logging
import streamlit as st
from textwrap import dedent
from typing import Dict, Any, Optional, List
from tempfile import TemporaryDirectory
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import AzureChatOpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TenderDocsSummaryUtils:

    def load_pdfs_to_docs(self, uploaded_pdfs) -> List[Document]:
        """
        Load multiple PDF files into a list of LangChain documents.

        Args:
            uploaded_pdfs: List of uploaded PDF files from Streamlit

        Returns:
            List[Document]: List of LangChain documents

        Raises:
            Exception: If there's an error processing any of the files
        """
        all_documents = []
        with TemporaryDirectory() as temp_dir:
            for file in uploaded_pdfs:
                try:
                    temp_path = os.path.join(temp_dir, file.name)
                    with open(temp_path, "wb") as temp_file:
                        temp_file.write(file.read())

                    loader = PyPDFLoader(file_path=temp_path)
                    documents = loader.load()
                    all_documents.extend(documents)

                except Exception as e:
                    logger.error(f"Error processing {file.name}: {e}")
                    continue

        return all_documents

    def concatenate_docs(
        self, documents: List[Document], include_metadata: bool = True
    ) -> str:
        """
        Concatenate multiple LangChain documents into a single string.

        Args:
            documents: List of LangChain documents
            include_metadata: Whether to include file name and page number in the output

        Returns:
            str: Concatenated document text
        """
        text_parts = []

        for i, doc in enumerate(documents):
            if include_metadata:
                source = doc.metadata.get("source", "")
                filename = source.split("/")[-1]
                text_parts.append(
                    f"### {filename} - Página {i + 1}\n{doc.page_content}"
                )
            else:
                text_parts.append(doc.page_content)

        return "\n\n".join(text_parts)


class TenderDocsSummaryChain:

    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment="gpt-4o",
            api_version="2024-08-01-preview",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def _run_section_categorization(self, tender_documents: str) -> str:
        """Run the analysis step of the chain."""

        messages = [
            {
                "role": "system",
                "content": "Você é um Analista de Editais especializado em obras públicas de saneamento.",
            },
            {
                "role": "user",
                "content": dedent(
                    f"""
                Analise os documentos de edital fornecidos (delimitados por <<<>>>) para identificar,
                categorizar e extrair as seções mais relevantes relacionadas a licitações para obras públicas
                em saneamento básico. Foque em prazos, condições financeiras, requisitos técnicos e legais.

                <tender_documents>
                {tender_documents}
                </tender_documents>

                Categorias esperadas:
                - prazos
                - financeiro
                - exigências legais
                - especificações técnicas
                - outros

                Formate sua resposta em markdown seguindo EXATAMENTE este modelo:
                <output_format>
                # Trecho 1
                - categoria: prazos
                - transcricao: [texto exato do edital]

                # Trecho 2
                - categoria: financeiro
                - transcricao: [texto exato do edital]

                # Trecho 3
                - categoria: exigências legais
                - transcricao: [texto exato do edital]
                </output_format>        
                """
                ),
            },
        ]

        categorized_sections = self.llm.invoke(messages)

        return categorized_sections

    def _run_requirements_step(self, categorized_sections: str) -> str:
        """Run the requirements step of the chain."""
        messages = [
            {
                "role": "system",
                "content": "Você é um Especialista em Requisitos e Conformidade para licitações públicas.",
            },
            {
                "role": "user",
                "content": dedent(
                    f"""
                Analise os trechos categorizados do edital e identifique os requisitos técnicos e legais
                para participação. Valide se os requisitos estão claros e categorize-os como itens de verificação.

                Trechos categorizados:
                {categorized_sections}

                Formate sua resposta em markdown seguindo EXATAMENTE este modelo:
                <<<
                # Requisito 1
                - categoria: [categoria]
                - descricao: [descrição clara e acionável]
                - origem: [seção/página do edital]

                # Requisito 2
                - categoria: [categoria]
                - descricao: [descrição clara e acionável]
                - origem: [seção/página do edital]
                >>>
                """
                ),
            },
        ]

        requirements_list = self.llm.invoke(messages)

        return requirements_list

    def _run_summary_step(self, requirements_list: str) -> str:
        """Run the summary step of the chain."""
        messages = [
            {
                "role": "system",
                "content": "Você é um Compilador e Validador de Relatórios especializado em licitações públicas.",
            },
            {
                "role": "user",
                "content": dedent(
                    f"""
                Com base nos requisitos identificados e na análise do edital, compile um relatório estruturado
                que inclua resumos, glossários e listas de verificação para submissão de propostas.

                Requisitos identificados:
                {requirements_list}

                Formate sua resposta em markdown seguindo EXATAMENTE este modelo:
                # Resumo Geral
                - [Resumo detalhado das seções principais]

                # Glossário
                - Termo 1: Definição
                - Termo 2: Definição

                # Checklist
                - [ ] [Requisito 1]
                - [ ] [Requisito 2]
                """
                ),
            },
        ]

        summary = self.llm.invoke(messages)

        return summary

    def generate_summary(self, tender_documents: str) -> str:
        """
        Generate and display the tender documents summary using Streamlit components.

        Args:
            tender_documents (str): The content of the tender documents to analyze

        Returns:
            str: The function returns the summary as a string
        """
        try:
            # Run the categorization step
            categorized_sections = self._run_section_categorization(tender_documents)

            # Run the requirements step
            requirements_list = self._run_requirements_step(categorized_sections)

            # Run the summary step
            summary_response = self._run_summary_step(requirements_list)
            summary = summary_response.content

            return summary

        except Exception as e:
            st.error(f"Erro ao gerar resumo: {str(e)}")
