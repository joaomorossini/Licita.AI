import logging
import os
from tempfile import TemporaryDirectory
from typing import List

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from openai import AzureOpenAI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TenderKnowledgeUtils:
    @staticmethod
    def load_pdfs_to_docs(uploaded_pdfs):
        logger.debug("Loading PDFs to documents")
        all_documents = []
        with TemporaryDirectory() as temp_dir:
            for uploaded_file in uploaded_pdfs:
                try:
                    temp_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_path, "wb") as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                    logger.debug(f"File written to temporary path: {temp_path}")

                    loader = PyPDFLoader(file_path=temp_path)
                    documents = loader.load()
                    logger.debug(
                        f"Loaded {len(documents)} documents from {uploaded_file.name}"
                    )
                    all_documents.extend(documents)
                except Exception as e:
                    logger.error(f"Error processing document: {e}")
                    continue

        logger.debug(f"Total documents loaded: {len(all_documents)}")
        return all_documents

    @staticmethod
    def concatenate_docs(documents):
        logger.debug("Concatenating documents")
        tender_documents = ""
        for i, doc in enumerate(documents):
            source = doc.metadata.get("source", "")
            filename = source.split("/")[-1]
            filename = filename.split(".")[0]
            tender_documents += f"{filename} - Pág.{i + 1}\n{doc.page_content}\n"
        logger.debug("All documents concatenated")
        return tender_documents

    @staticmethod
    def _length_function(text: str, encoding: str = "o200k_base") -> int:
        enc = tiktoken.get_encoding(f"{encoding}")
        return len(enc.encode(text))

    @staticmethod
    def split_text(text: str) -> List[str]:
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=2500,
            chunk_overlap=250,
            length_function=TenderKnowledgeUtils._length_function,
        )
        chunks = splitter.split_text(text=text)
        return chunks

    @staticmethod
    def get_embeddings(text, model="text-embedding-3-large"):
        client = AzureOpenAI(
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
        response = client.embeddings.create(input=text, model=model)
        return response
