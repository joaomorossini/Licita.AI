from typing import List, Dict, Optional, Callable
import re
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from pdfminer.high_level import extract_text
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
import asyncio
from tqdm.asyncio import tqdm_asyncio
import streamlit as st

# Configure logging to only show INFO and above
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class TenderNotice:
    """Represents a single tender notice extracted from an email digest."""
    organization: str
    type: str
    city: str
    state: str
    modality: str
    number: str
    object_description: str
    segmentation: str
    opening_date: Optional[datetime]
    id_universo: str
    phones: List[str]
    access_info: List[str]
    complementary_info: str
    label: Optional[str] = None
    
class TenderNoticeProcessor:
    """Processes tender notices from email PDFs."""
    
    def __init__(self, llm: AzureChatOpenAI, batch_size: int = 5):
        self.llm = llm
        self.batch_size = batch_size
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def _extract_tender_blocks(self, text: str) -> List[str]:
        """Extracts individual tender blocks from the email text."""
        logging.info("Starting tender block extraction")
        
        # Clean the text (preserve structure)
        text = text.replace('\\n', '\n')   # Fix escaped newlines
        text = re.sub(r'\n\s+', '\n', text)  # Remove leading spaces after newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Normalize horizontal whitespace only
        
        # Log the first 500 chars to see the structure
        logging.info(f"First 500 chars after cleaning: {text[:500]}")
        
        # Primary pattern: Look for blocks that start with organization and contain key fields
        blocks = []
        
        # Split on organization headers first
        org_pattern = r'\n[A-ZÇÁÉÍÓÚÂÊÎÔÛÃÕ][^\n]+?\([0-9]+/[0-9]+\)'
        potential_blocks = re.split(org_pattern, text)
        
        # If we found blocks with org headers
        if len(potential_blocks) > 1:
            # First element is before first match, skip if empty
            if potential_blocks[0].strip():
                blocks.extend([potential_blocks[0]])
            
            # Reconstruct blocks with their headers
            headers = re.findall(org_pattern, text)
            for header, content in zip(headers, potential_blocks[1:]):
                blocks.append(f"{header.strip()}\n{content.strip()}")
        else:
            # Fallback: try splitting on field markers
            field_pattern = r'\n(?=Tipo de Órgão:|Modalidade:)'
            blocks = [b.strip() for b in re.split(field_pattern, text) if b.strip()]
        
        logging.info(f"Found {len(blocks)} potential blocks")
        
        # Validate blocks
        valid_blocks = []
        required_fields = ['Tipo de Órgão:', 'Modalidade:', 'Objeto:']
        
        for block in blocks:
            # Must have at least 2 required fields and be long enough
            if sum(1 for field in required_fields if field in block) >= 2 and len(block.split()) > 20:
                valid_blocks.append(block)
        
        logging.info(f"Extracted {len(valid_blocks)} valid blocks")
        return valid_blocks
    
    def _parse_tender_block(self, block: str) -> TenderNotice:
        """Parses a single tender block into structured data."""
        # Helper function to safely extract field with multiple patterns
        def extract_field(patterns: List[str], default: str = "") -> str:
            for pattern in patterns:
                match = re.search(pattern, block, re.DOTALL | re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if value:  # Only return if non-empty
                        return value
            return default
        
        try:
            # Extract organization (try multiple patterns)
            org_patterns = [
                r'^\s*([A-ZÇÁÉÍÓÚÂÊÎÔÛÃÕ][^(]+?)(?:\s*\([0-9]+/[0-9]+\)|\s*$)',
                r'^\s*([A-ZÇÁÉÍÓÚÂÊÎÔÛÃÕ][^(]+?)(?:\s*-\s*[A-Za-zçáéíóúâêîôûãõ\s]+)',
                r'(?:Órgão:|Entidade:)\s*([^\n]+)'
            ]
            organization = ""
            for pattern in org_patterns:
                match = re.search(pattern, block, re.DOTALL)
                if match:
                    organization = match.group(1).strip()
                    if organization and not organization.startswith("Tipo de"):
                        break
            
            # Extract type
            type_patterns = [
                r'Tipo de Órgão:\s*([^\n]+?)(?=\s+Cidade:)',
                r'Tipo de Órgão:\s*([^\n]+)',  # Fallback without Cidade
                r'Tipo:\s*([^\n]+)'
            ]
            org_type = extract_field(type_patterns)
            
            # Extract city and state
            city_state_patterns = [
                r'Cidade:\s*([^,\n]+?)\s*,?\s*([A-Z]{2})',
                r'Local:\s*([^,\n]+?)\s*,?\s*([A-Z]{2})'
            ]
            city = state = ""
            for pattern in city_state_patterns:
                match = re.search(pattern, block)
                if match:
                    city, state = match.groups()
                    city = city.strip()
                    state = state.strip()
                    break
            
            # Extract modality and number
            modality = extract_field([
                r'Modalidade:\s*([^\n]+?)(?=\s+Nº:)',
                r'Modalidade:\s*([^\n]+)'
            ])
            
            number = extract_field([
                r'Nº:\s*([\d\-/]+)',
                r'Número:\s*([\d\-/]+)'
            ])
            
            # Extract object description (more robust pattern)
            obj_patterns = [
                r'Objeto:(.+?)(?=(?:Segmentação:|Abertura:|Telefone:|ID Universo:))',
                r'Objeto:(.+?)(?=\n\n)',
                r'Objeto:(.+)'  # Fallback pattern
            ]
            object_description = extract_field(obj_patterns)
            
            # Extract segmentation
            seg_patterns = [
                r'Segmentação:(.+?)(?=(?:Abertura:|ID Universo:|Telefone:))',
                r'Segmentação:(.+?)(?=\n\n)',
                r'Segmentação:(.+)'
            ]
            segmentation = extract_field(seg_patterns)
            
            # Extract opening date
            opening_date = None
            date_patterns = [
                r'Abertura:\s*([\d/]+\s+[\d:]+)',
                r'Data de Abertura:\s*([\d/]+\s+[\d:]+)'
            ]
            date_str = extract_field(date_patterns)
            if date_str:
                try:
                    opening_date = datetime.strptime(date_str.strip(), '%d/%m/%Y %H:%M')
                except ValueError:
                    logging.warning(f"Failed to parse opening date: {date_str}")
            
            # Extract ID
            id_universo = extract_field([
                r'ID Universo:\s*(\d+)',
                r'ID:\s*(\d+)'
            ])
            
            # Extract phones
            phones = []
            phone_matches = re.finditer(r'(?:Telefone|Fone|Tel)(?:\s+\d+)?:\s*([\d\(\)\s\-]+)', block)
            for match in phone_matches:
                phone = match.group(1).strip()
                if phone and phone not in phones:
                    phones.append(phone)
            
            # Extract access info
            access_info = []
            access_block = re.search(r'Acesso:(.+?)(?=(?:Complementos:|$))', block, re.DOTALL)
            if access_block:
                # Split by common URL/email patterns and clean
                items = re.split(r'[\n,]', access_block.group(1))
                for item in items:
                    item = item.strip('- ').strip()
                    if item and item not in access_info:
                        access_info.append(item)
            
            # Extract complementary info
            complementary_info = extract_field([
                r'Complementos:(.+?)(?=(?:Data Cadastro:|$))',
                r'Complementos:(.+)'
            ])
            
            # Create TenderNotice object
            tender = TenderNotice(
                organization=organization,
                type=org_type,
                city=city,
                state=state,
                modality=modality,
                number=number,
                object_description=object_description,
                segmentation=segmentation,
                opening_date=opening_date,
                id_universo=id_universo,
                phones=phones,
                access_info=access_info,
                complementary_info=complementary_info
            )
            
            return tender
            
        except Exception as e:
            logging.error(f"Error parsing tender block: {str(e)}")
            raise
    
    async def _label_tender_batch(self, tenders: List[TenderNotice], template: str, company_description: str) -> None:
        """Labels a batch of tenders using the LLM in parallel."""
        tasks = []
        for tender in tenders:
            # Create tender notice text for LLM
            notice_text = f"""
            Organization: {tender.organization}
            Type: {tender.type}
            Location: {tender.city}, {tender.state}
            Modality: {tender.modality} {tender.number}
            
            Object Description:
            {tender.object_description}
            
            Segmentation:
            {tender.segmentation}
            """
            
            # Create prompt and get response directly from LLM
            prompt = ChatPromptTemplate.from_template(template)
            messages = prompt.format_messages(
                company_business_description=company_description,
                tender_notice=notice_text
            )
            tasks.append(self.llm.ainvoke(messages))
        
        # Process all tasks in parallel
        responses = await asyncio.gather(*tasks)
        
        # Extract labels from responses
        for tender, response in zip(tenders, responses):
            label_match = re.search(r'(yes|no|unsure)', response.content.lower())
            tender.label = label_match.group(1) if label_match else 'unsure'
    
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
            
            # Show extracted text in UI
            with st.expander("Extracted Text Content", expanded=False):
                st.text(text)
            
            # Extract tender blocks
            blocks = self._extract_tender_blocks(text)
            
            # Parse blocks into TenderNotice objects
            tenders = []
            for i, block in enumerate(blocks, 1):
                logging.info(f"Processing block {i}/{len(blocks)}")
                logging.info(f"Block content: {block[:200]}...")  # Log first 200 chars
                
                try:
                    tender = self._parse_tender_block(block)
                    if tender:
                        tenders.append(tender)
                        if progress_callback:
                            progress_callback(f"Processed tender {i}/{len(blocks)}: {tender.organization}")
                except Exception as e:
                    logging.error(f"Error processing block {i}: {str(e)}")
                    logging.error(f"Block content: {block}")
            
            # Process tenders in batches with semaphore to limit concurrency
            semaphore = asyncio.Semaphore(max_concurrent_chunks)
            total_batches = (len(tenders) + self.batch_size - 1) // self.batch_size
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            async def process_batch(batch_index: int, batch: List[TenderNotice]):
                async with semaphore:
                    status_text.text(f"Processing batch {batch_index + 1} of {total_batches}...")
                    await self._label_tender_batch(batch, template, company_description)
                    progress = (batch_index + 1) / total_batches
                    progress_bar.progress(progress)
                    if progress_callback:
                        progress_callback(f"Processed batch {batch_index + 1} of {total_batches}")
            
            # Create tasks for all batches
            tasks = []
            for i in range(0, len(tenders), self.batch_size):
                batch = tenders[i:i + self.batch_size]
                tasks.append(process_batch(i // self.batch_size, batch))
            
            # Process all batches
            await asyncio.gather(*tasks)
            
            progress_bar.progress(1.0)
            status_text.text("Processing completed!")
            
            # Convert to DataFrame
            df = pd.DataFrame([vars(t) for t in tenders])
            
            # Sort by label priority (yes > maybe > no)
            label_priority = {'yes': 0, 'unsure': 1, 'no': 2}
            df['label_priority'] = df['label'].map(label_priority)
            df = df.sort_values('label_priority').drop('label_priority', axis=1)
            
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
    
    # Create LLM instance
    llm = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="gpt-4o",
        temperature=0
    )
    
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
    
    processor = TenderNoticeProcessor(llm=llm)
    
    async def main():
        tenders = await processor.process_pdf(pdf_path, template, company_description)
        print(f"\nProcessed {len(tenders)} tenders:")
        for tender in tenders:
            print(f"\n{tender}")
    
    asyncio.run(main())

