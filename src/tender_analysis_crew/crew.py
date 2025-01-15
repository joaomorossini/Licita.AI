import os
from tempfile import TemporaryDirectory, NamedTemporaryFile
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from crewai import Crew, Process
from crewai.llm import LLM
import tiktoken
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI
from langchain.schema import BaseOutputParser
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.tender_analysis_crew.templates.extract_and_label_sections_template import (
    extract_and_label_sections_template,
    extract_and_label_sections_json_schema,
)
from src.tender_analysis_crew.agents import (
    analista_de_licitacoes,
    compilador_de_relatorio,
    revisor_de_relatório,
)
from src.tender_analysis_crew.tasks import (
    analise_de_licitacao,
    montagem_de_cronograma,
    compilacao_de_relatorio,
    revisao_de_relatorio,
)

# Load environment variables
load_dotenv()

llm = LLM(
    # model="gemini/gemini-1.5-pro-latest",
    model="azure/gpt-4o",
    temperature=0.2,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TenderAnalysisUtils:
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
            chunk_size=2000,
            chunk_overlap=200,
            length_function=TenderAnalysisUtils._length_function,
        )
        chunks = splitter.split_text(text=text)
        return chunks


class TenderAnalysisCrew:
    def __init__(self):
        logger.debug("Initializing TendersAnalysisCrew")
        self.crew = Crew(
            agents=[
                analista_de_licitacoes,
                compilador_de_relatorio,
                revisor_de_relatório,
            ],
            tasks=[
                analise_de_licitacao,
                montagem_de_cronograma,
                compilacao_de_relatorio,
                revisao_de_relatorio,
            ],
            process=Process.sequential,
            verbose=True,
            planning=False,
            memory=False,
            tools=[],
            manager_llm=llm,
            function_calling_llm=llm,
        )
        logger.debug("Crew initialized with agents and tasks")

    def extract_and_label_sections(
        self,
        tender_documents_chunk_text: str,
        prompt_template: Optional[str] = extract_and_label_sections_template,
        json_schema: Optional[Dict[str, Any]] = extract_and_label_sections_json_schema,
    ) -> List[Dict[str, str]]:

        # Classify each relevant section in the chunk into pre-defined labels
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Instantiate the language model
        model = AzureChatOpenAI(
            model="gpt-4o-mini", azure_deployment="gpt-4o-mini", temperature=0
        )

        # Enforce structured output with json schema
        structured_model = model.with_structured_output(json_schema)

        # Chain the prompt and the model
        chain = prompt | structured_model

        # Invoke the chain
        response = chain.invoke(  # TODO: Test with '.stream' method
            {
                "tender_documents_chunk_text": tender_documents_chunk_text,
            }
        )
        # labeled_tender_documents_sections = response.content
        # return labeled_tender_documents_sections
        return response

    # TODO: Implement this method. Review the Crew inputs and outputs
    def generate_summary(self, labeled_tender_documents_sections: List[Dict[str, str]]):
        logger.debug("Generating summary")
        crew_input = {
            "labeled_tender_documents_sections": labeled_tender_documents_sections,
        }
        logger.debug("Crew input prepared for kickoff")
        summary = self.crew.kickoff(inputs=crew_input)
        logger.debug("Summary generated")
        return summary
