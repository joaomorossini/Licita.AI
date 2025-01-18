import os
import time
import logging
import asyncio
from datetime import datetime
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import tiktoken
from dotenv import load_dotenv
from crewai import Crew, Process
from crewai.llm import LLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI
from langchain.schema import BaseOutputParser
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.utils import TenderKnowledgeUtils
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


class TenderAnalysisCrew:
    def __init__(self):
        logger.debug("Initializing TendersAnalysisCrew")
        self.env = os.getenv("ENVIRONMENT", "prod")
        self.crew = Crew(
            agents=[
                compilador_de_relatorio,
                revisor_de_relatório,
            ],
            tasks=[
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
            output_log_file=(
                f"src/tender_analysis_crew/outputs/tender_analysis_crew_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.log"
                if self.env == "prod"
                else None
            ),
            task_execution_output_json_files=(
                [
                    f"src/tender_analysis_crew/outputs/task_execution_output_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
                ]
                if self.env == "prod"
                else None
            ),
        )
        self.utils = TenderKnowledgeUtils()
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
        max_concurrent_chunks: int = 10,
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
        logger.debug("Generating summary")

        # Create execution times log file
        execution_log_path = f"src/tender_analysis_crew/outputs/execution_times_logs-{datetime.now().strftime('%Y-%m-%d_%H-%M')}.log"
        with open(execution_log_path, "w") as log_file:
            log_file.write(
                f"Execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            # Split text into chunks
            split_start = time.time()
            chunks = self.utils.split_text(tender_documents_text)
            split_time = time.time() - split_start
            logger.debug(f"Split text into {len(chunks)} chunks")
            log_file.write(f"Text splitting time: {split_time:.2f} seconds\n")
            log_file.write(f"Number of chunks: {len(chunks)}\n\n")

            # Process chunks in batches
            chunk_results = []
            processed_chunks = 0
            total_chunks = len(chunks)

            # Process chunks in batches of max_concurrent_chunks
            for i in range(0, total_chunks, max_concurrent_chunks):
                batch = chunks[i : i + max_concurrent_chunks]
                batch_tasks = []

                # Create tasks for the current batch
                for chunk in batch:
                    task = asyncio.create_task(self._extract_and_label_sections(chunk))
                    batch_tasks.append(task)

                # Wait for the current batch to complete
                batch_results = await asyncio.gather(*batch_tasks)
                chunk_results.extend(batch_results)

                # Update progress for completed chunks
                processed_chunks += len(batch)
                if progress_callback:
                    progress_callback(min(processed_chunks, total_chunks))

                # Log processing time for the batch
                batch_time = time.time() - start_time
                log_file.write(
                    f"Batch {i//max_concurrent_chunks + 1} processing time: {batch_time:.2f} seconds\n"
                )

            # Combine results from all chunks
            combine_start = time.time()
            labeled_sections = self._combine_labeled_sections(chunk_results)
            combine_time = time.time() - combine_start
            logger.debug("Combined results from all chunks")
            log_file.write(f"\nCombining results time: {combine_time:.2f} seconds\n")

            # Filter sections by category
            filter_start = time.time()
            filtered_sections = self._filter_sections_by_category(labeled_sections)
            filter_time = time.time() - filter_start
            log_file.write(f"Filtering sections time: {filter_time:.2f} seconds\n")

            # Rest of the processing
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
                if k
                in [
                    "requisitos_tecnicos",
                    "economicos_financeiros",
                    "oportunidades",
                    "outros_requisitos",
                ]
            }.items():
                if sections:
                    technical_sections_str += f"\n{category.upper()}:\n"
                    technical_sections_str += "\n".join(
                        self._format_section(s) for s in sections
                    )

            cronograma_sections_str = "Seções de Cronograma:\n"
            cronograma_sections_str += "\n".join(
                self._format_section(s)
                for s in filtered_sections["prazos_e_cronograma"]
            )

            all_sections_str = "Todas as Seções:\n"
            for category, sections in filtered_sections.items():
                if sections:
                    all_sections_str += f"\n{category.upper()}:\n"
                    all_sections_str += "\n".join(
                        self._format_section(s) for s in sections
                    )
            format_time = time.time() - format_start
            log_file.write(f"Formatting sections time: {format_time:.2f} seconds\n")

            # Prepare and execute crew tasks
            crew_start = time.time()
            crew_input = {
                "cronograma_sections": cronograma_sections_str,
                "technical_sections": technical_sections_str,
                "all_sections": all_sections_str,
                "overview": overview_str,
            }

            logger.debug("Crew input prepared for kickoff")
            summary = self.crew.kickoff(inputs=crew_input)
            crew_time = time.time() - crew_start
            log_file.write(f"Crew execution time: {crew_time:.2f} seconds\n")

            # Total execution time
            total_time = time.time() - start_time
            log_file.write(f"\nTotal execution time: {total_time:.2f} seconds\n")

        logger.debug("Summary generated")
        return summary
