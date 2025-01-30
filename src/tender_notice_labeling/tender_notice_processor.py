from typing import List, Dict, Optional, Callable, Any
import re
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from pdfminer.high_level import extract_text
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import logging
import asyncio
from tqdm.asyncio import tqdm_asyncio
import streamlit as st
import json

from .tender_notice_templates import (
    TENDER_NOTICE_EXTRACTION_SCHEMA,
    TENDER_NOTICE_EXTRACTION_PROMPT,
)

# Configure logging to only show INFO and above
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class TenderNotice:
    """Represents a single tender notice extracted from an email digest."""
    num_seq_boletim: str
    orgao: str
    estado: str
    numero_licitacao: str
    objeto: str
    data_hora_licitacao: str
    id_universo: int
    data_hora_alteracao: str
    label: Optional[str] = None

class TenderNoticeProcessor:
    """Processes tender notices from email PDFs."""
    
    def __init__(self, batch_size: int = 5):
        # Initialize LLM for extraction
        self.extraction_llm = AzureChatOpenAI(
            model="gpt-4o",
            azure_deployment="gpt-4o",
            temperature=0
        ).with_structured_output(TENDER_NOTICE_EXTRACTION_SCHEMA)
        
        # Initialize LLM for labeling
        self.labeling_llm = AzureChatOpenAI(
            model="gpt-4o",
            azure_deployment="gpt-4o",
            temperature=0
        )
        
        self.batch_size = batch_size

    async def _extract_tender_notices(self, text: str) -> List[Dict[str, Any]]:
        """Extracts tender notices from text using structured LLM output."""
        logging.info("Starting tender notice extraction")
        
        # Create prompt and get structured response
        prompt = ChatPromptTemplate.from_template(TENDER_NOTICE_EXTRACTION_PROMPT)
        messages = prompt.format_messages(tender_notices_text=text)
        
        try:
            response = await self.extraction_llm.ainvoke(messages)
            return response["boletins_de_licitacoes"]
        except Exception as e:
            logging.error(f"Error extracting tender notices: {str(e)}")
            raise
    
    async def _label_tender_batch(self, tenders: List[Dict[str, Any]], template: str, company_description: str) -> None:
        """Labels a batch of tenders using the LLM in parallel."""
        tasks = []
        for tender in tenders:
            # Create tender notice text for LLM
            notice_text = f"""
            Organization: {tender['orgao']}
            Location: {tender['estado']}
            Number: {tender['numero_licitacao']}
            
            Object Description:
            {tender['objeto']}
            
            Opening Date: {tender['data_hora_licitacao']}
            """
            
            # Create prompt and get response directly from LLM
            prompt = ChatPromptTemplate.from_template(template)
            messages = prompt.format_messages(
                company_business_description=company_description,
                tender_notice=notice_text
            )
            tasks.append(self.labeling_llm.ainvoke(messages))
        
        # Process all tasks in parallel
        responses = await asyncio.gather(*tasks)
        
        # Extract labels from responses and update tenders
        for tender, response in zip(tenders, responses):
            label_match = re.search(r'(yes|no|unsure)', response.content.lower())
            tender['label'] = label_match.group(1) if label_match else 'unsure'
    
    async def process_pdf(
        self, 
        pdf_path: str, 
        template: str, 
        company_description: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_concurrent_chunks: int = 5
    ) -> pd.DataFrame:
        """Processes a PDF containing tender notices with async batch processing."""
        logging.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Extract text from PDF
            text = extract_text(pdf_path)
            
            # Extract tender notices using structured output
            tender_notices = await self._extract_tender_notices(text)
            
            # Process tenders in batches with semaphore to limit concurrency
            semaphore = asyncio.Semaphore(max_concurrent_chunks)
            total_batches = (len(tender_notices) + self.batch_size - 1) // self.batch_size
            
            async def process_batch(batch_index: int, batch: List[Dict[str, Any]]):
                async with semaphore:
                    if progress_callback:
                        progress_callback(f"Processing batch {batch_index + 1} of {total_batches}...")
                    await self._label_tender_batch(batch, template, company_description)
                    if progress_callback:
                        progress_callback(f"Processed batch {batch_index + 1} of {total_batches}")
            
            # Create tasks for all batches
            tasks = []
            for i in range(0, len(tender_notices), self.batch_size):
                batch = tender_notices[i:i + self.batch_size]
                tasks.append(process_batch(i // self.batch_size, batch))
            
            # Process all batches
            await asyncio.gather(*tasks)
            
            if progress_callback:
                progress_callback("Processing completed!")
            
            # Convert to DataFrame
            df = pd.DataFrame(tender_notices)
            
            # Clean up and standardize labels
            label_map = {
                'yes': '✅ Participar',
                'no': '❌ Declinar',
                'unsure': '🤔 Avaliar',
                'insufficient_info': '🤷‍♂️ Info insuficiente',
                None: '🤔 Avaliar'  # Default to 'Avaliar'
            }
            df['label'] = df['label'].map(lambda x: label_map.get(x, '🤔 Avaliar'))
            
            # Sort by label priority and opening date
            label_priority = {
                '✅ Participar': 0,
                '🤔 Avaliar': 1,
                '❌ Declinar': 2,
                '🤷‍♂️ Info insuficiente': 3
            }
            df['label_priority'] = df['label'].map(label_priority)
            df = df.sort_values(['label_priority', 'data_hora_licitacao'], ascending=[True, True], na_position='last')
            df = df.drop('label_priority', axis=1)
            
            return df
            
        except Exception as e:
            logging.error(f"Error processing PDF: {str(e)}")
            raise

if __name__ == "__main__":
    import sys
    import asyncio
    import os
    from langchain_openai import AzureChatOpenAI
    
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) != 2:
        print("Usage: python tender_notice_processor.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Test data
    template = """
    Você é um especialista em análise de licitações. Sua tarefa é analisar o edital de licitação fornecido e determinar se a empresa deve participar com base nos seguintes critérios:
    
    1. A empresa atua no setor de engenharia e construção civil, com foco em:
       - Obras de infraestrutura
       - Construção de edifícios
       - Reformas e adaptações
       - Instalações elétricas e hidráulicas
    
    2. A empresa tem capacidade para executar obras de até R$ 10 milhões
    
    3. A empresa atua principalmente nos estados: SP, RJ, MG, PR, SC
    
    Analise o edital e responda apenas "yes" se a empresa deve participar, "no" se não deve participar, ou "maybe" se precisar de mais informações.
    """
    
    company_description = """
    Empresa de engenharia e construção civil com 15 anos de experiência.
    Principais áreas de atuação:
    - Obras de infraestrutura
    - Construção de edifícios
    - Reformas e adaptações
    - Instalações elétricas e hidráulicas
    
    Capacidade de execução: Até R$ 10 milhões por obra
    Região de atuação: SP, RJ, MG, PR, SC
    """
    
    processor = TenderNoticeProcessor()
    
    async def main():
        df = await processor.process_pdf(pdf_path, template, company_description)
        print(f"\nProcessed {len(df)} tenders")
        print(df)
    
    asyncio.run(main())

