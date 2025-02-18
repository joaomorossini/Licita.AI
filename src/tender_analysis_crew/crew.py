from datetime import datetime
import os
from tempfile import TemporaryDirectory, NamedTemporaryFile
import logging
from typing import Any, Dict, List, Optional, Callable
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
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

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
    montagem_de_cronograma,
    esboco_do_relatorio,
    revisao_final_do_relatorio,
)

# Load environment variables
load_dotenv()


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

llm = LLM(
    model=os.getenv("TENDER_ANALYSIS_CREW_MANAGER_MODEL", "azure/gpt-4o"),
    temperature=float(os.getenv("TENDER_ANALYSIS_CREW_MANAGER_TEMPERATURE", 0.2)),
)

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
            chunk_size=2500,
            chunk_overlap=250,
            length_function=TenderAnalysisUtils._length_function,
        )
        chunks = splitter.split_text(text=text)
        return chunks


class TenderAnalysisCrew:
    def __init__(self):
        logger.debug("Initializing TendersAnalysisCrew")
        self.env = os.getenv("ENVIRONMENT", "prod")
        self.crew = Crew(
            agents=[
                analista_de_licitacoes,
                compilador_de_relatorio,
                revisor_de_relatório,
            ],
            tasks=[
                montagem_de_cronograma,
                esboco_do_relatorio,
                revisao_final_do_relatorio,
            ],
            process=Process.sequential,
            verbose=True,
            planning=False,
            memory=False,
            tools=[],
            manager_llm=llm,
            function_calling_llm=llm,
            output_log_file=(
                f"src/tender_analysis_crew/outputs/tender_analysis_crew_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.log"
                if self.env == "dev"
                else None
            ),
            task_execution_output_json_files=(
                [
                    f"src/tender_analysis_crew/outputs/task_execution_output_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
                ]
                if self.env == "dev"
                else None
            ),
        )
        self.utils = TenderAnalysisUtils()
        logger.debug("Crew initialized with agents and tasks")

    def _format_section(self, section: Dict[str, Any]) -> str:
        """Format a section dictionary into a readable string.

        Args:
            section: Dictionary containing section data with categoria, checklist, transcricao, and optional comentario

        Returns:
            str: Formatted string representation of the section
        """
        return f"""
        Categoria: {section['categoria']}
        Checklist: {'Sim' if section['checklist'] == 1 else 'Não'}
        Transcrição: {section['transcricao']}
        {f"Comentário: {section['comentario']}" if 'comentario' in section else ''}
        """

    def _combine_labeled_sections(
        self, chunk_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Combine labeled sections from multiple chunks into a single result.

        Args:
            chunk_results: List of results from _extract_and_label_sections for each chunk

        Returns:
            Dict containing combined 'sections' and the last non-empty 'overview'
        """
        logger.debug("Combining labeled sections from chunks")

        # Initialize combined result
        combined_result = {"sections": [], "overview": {}}

        # Combine sections from all chunks
        for result in chunk_results:
            if result.get("sections"):
                combined_result["sections"].extend(result["sections"])

            # Keep the last non-empty overview
            if result.get("overview", {}).get("client_name"):
                combined_result["overview"] = result["overview"]

        logger.debug(
            f"Combined {len(combined_result['sections'])} sections from chunks"
        )
        return combined_result

    async def _extract_and_label_sections(
        self,
        tender_documents_chunk_text: str,
        prompt_template: Optional[str] = extract_and_label_sections_template,
        json_schema: Optional[Dict[str, Any]] = extract_and_label_sections_json_schema,
    ) -> Dict[str, Any]:
        """Extract and label sections from tender documents asynchronously.

        Args:
            tender_documents_chunk_text: The text to analyze
            prompt_template: Template for the extraction prompt
            json_schema: Schema for structured output

        Returns:
            Dict containing 'sections' and 'overview' data
        """
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

        # Invoke the chain asynchronously
        response = await chain.ainvoke(
            {
                "tender_documents_chunk_text": tender_documents_chunk_text,
            }
        )
        return response

    def _filter_sections_by_category(
        self, labeled_sections: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Filter sections by category for task-specific processing.

        Args:
            labeled_sections: The labeled sections from _extract_and_label_sections

        Returns:
            Dict mapping categories to their respective sections
        """
        logger.debug("Filtering sections by category")
        filtered_sections = {
            "prazos_e_cronograma": [],
            "requisitos_tecnicos": [],
            "economicos_financeiros": [],
            "riscos": [],
            "oportunidades": [],
            "outros_requisitos": [],
            "outras_informacoes_relevantes": [],
        }

        # Extract sections from the response
        sections = labeled_sections.get("sections", [])

        # Filter sections by category
        for section in sections:
            category = section.get("categoria")
            if category in filtered_sections:
                filtered_sections[category].append(section)

        logger.debug("Sections filtered by category")
        return filtered_sections

    async def generate_summary(
        self,
        tender_documents_text: str,
        progress_callback: Optional[Callable[[int], None]] = None,
        max_concurrent_chunks: int = int(os.getenv("TENDER_ANALYSIS_MAX_CONCURRENT_CHUNKS", 10)),
    ) -> str:
        """Generate a summary of tender documents.

        Args:
            tender_documents_text: The text content of tender documents
            progress_callback: Optional callback function to report progress (receives current chunk number)
            max_concurrent_chunks: Maximum number of chunks to process concurrently (default: 10)

        Returns:
            str: The generated summary
        """
        start_time = time.time()
        logger.info("Starting summary generation")

        # Initialize timing metrics
        timing_metrics = {
            "split_time": 0,
            "batch_processing_time": 0,
            "combine_time": 0,
            "filter_time": 0,
            "format_time": 0,
            "crew_time": 0
        }

        try:
            # Split text into chunks
            split_start = time.time()
            chunks = self.utils.split_text(tender_documents_text)
            timing_metrics["split_time"] = time.time() - split_start
            logger.info(f"Split text into {len(chunks)} chunks in {timing_metrics['split_time']:.2f} seconds")

            # Process chunks in batches
            chunk_results = []
            processed_chunks = 0
            total_chunks = len(chunks)
            batch_start = time.time()

            # Process chunks in batches of max_concurrent_chunks
            for i in range(0, total_chunks, max_concurrent_chunks):
                batch = chunks[i : i + max_concurrent_chunks]
                batch_tasks = []

                # Create tasks for the current batch
                # TODO: Adicionar chunk_id para identificar e facilitar o refenciamento dos trechos
                for chunk in batch:
                    task = asyncio.create_task(self._extract_and_label_sections(chunk))
                    batch_tasks.append(task)

                try:
                    # Wait for the current batch to complete
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    # Handle any exceptions from batch processing
                    for result in batch_results:
                        if isinstance(result, Exception):
                            logger.error(f"Error processing batch: {str(result)}")
                            raise result
                        
                    chunk_results.extend(batch_results)

                    # Update progress for completed chunks
                    processed_chunks += len(batch)
                    if progress_callback:
                        progress_callback(min(processed_chunks, total_chunks))

                    logger.debug(f"Processed batch {i//max_concurrent_chunks + 1}/{(total_chunks + max_concurrent_chunks - 1)//max_concurrent_chunks}")
                except Exception as e:
                    logger.error(f"Error processing batch {i//max_concurrent_chunks + 1}: {str(e)}")
                    raise

            timing_metrics["batch_processing_time"] = time.time() - batch_start
            logger.info(f"Processed all chunks in {timing_metrics['batch_processing_time']:.2f} seconds")

            # Combine results from all chunks
            combine_start = time.time()
            labeled_sections = self._combine_labeled_sections(chunk_results)
            timing_metrics["combine_time"] = time.time() - combine_start
            logger.info(f"Combined results in {timing_metrics['combine_time']:.2f} seconds")

            # Filter sections by category
            filter_start = time.time()
            filtered_sections = self._filter_sections_by_category(labeled_sections)
            timing_metrics["filter_time"] = time.time() - filter_start
            logger.info(f"Filtered sections in {timing_metrics['filter_time']:.2f} seconds")

            # Format sections
            format_start = time.time()
            overview_str = f"""
            Cliente: {labeled_sections['overview']['client_name']}
            ID da Licitação: {labeled_sections['overview']['tender_id']}
            Data: {labeled_sections['overview'].get('tender_date', 'Não especificada')}
            Objeto: {labeled_sections['overview']['tender_object']}
            """

            technical_sections_str = "Seções Técnicas:\n"
            for category, sections in {
                k: v
                for k, v in filtered_sections.items()
                if k in ["requisitos_tecnicos", "economicos_financeiros", "oportunidades", "outros_requisitos"]
            }.items():
                if sections:
                    technical_sections_str += f"\n{category.upper()}:\n"
                    technical_sections_str += "\n".join(self._format_section(s) for s in sections)

            cronograma_sections_str = "Seções de Cronograma:\n"
            cronograma_sections_str += "\n".join(
                self._format_section(s) for s in filtered_sections["prazos_e_cronograma"]
            )

            all_sections_str = "Todas as Seções:\n"
            for category, sections in filtered_sections.items():
                if sections:
                    all_sections_str += f"\n{category.upper()}:\n"
                    all_sections_str += "\n".join(self._format_section(s) for s in sections)

            timing_metrics["format_time"] = time.time() - format_start
            logger.info(f"Formatted sections in {timing_metrics['format_time']:.2f} seconds")

            # Prepare and execute crew tasks
            crew_start = time.time()
            crew_input = {
                "cronograma_sections": cronograma_sections_str,
                "technical_sections": technical_sections_str,
                "all_sections": all_sections_str,
                "overview": overview_str,
            }

            logger.info("Starting crew execution")
            summary = self.crew.kickoff(inputs=crew_input)
            timing_metrics["crew_time"] = time.time() - crew_start
            logger.info(f"Crew execution completed in {timing_metrics['crew_time']:.2f} seconds")

            # Log total execution time and return summary
            total_time = time.time() - start_time
            logger.info(f"Total summary generation time: {total_time:.2f} seconds")

            # If in dev environment, write detailed timing metrics to file
            if self.env == "dev":
                log_dir = "src/tender_analysis_crew/outputs"
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, f"execution_times_logs-{datetime.now().strftime('%Y-%m-%d_%H-%M')}.log")
                
                with open(log_path, "w") as log_file:
                    log_file.write(f"Execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    log_file.write(f"Text splitting time: {timing_metrics['split_time']:.2f} seconds\n")
                    log_file.write(f"Batch processing time: {timing_metrics['batch_processing_time']:.2f} seconds\n")
                    log_file.write(f"Combining results time: {timing_metrics['combine_time']:.2f} seconds\n")
                    log_file.write(f"Filtering sections time: {timing_metrics['filter_time']:.2f} seconds\n")
                    log_file.write(f"Formatting sections time: {timing_metrics['format_time']:.2f} seconds\n")
                    log_file.write(f"Crew execution time: {timing_metrics['crew_time']:.2f} seconds\n")
                    log_file.write(f"\nTotal execution time: {total_time:.2f} seconds\n")

            return summary

        except Exception as e:
            logger.error(f"Error in generate_summary: {str(e)}", exc_info=True)
            raise
