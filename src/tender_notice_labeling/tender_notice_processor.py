from typing import List, Dict, Optional
import re
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.chat_models import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    
    def __init__(self, llm: AzureChatOpenAI):
        self.llm = llm
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def _extract_tender_blocks(self, text: str) -> List[str]:
        """Extracts individual tender blocks from the email text using regex to identify headers."""
        # Debug: Print the raw text being processed
        print("\nRaw text being processed:")
        print(text)

        # Split the raw text into individual tenders based on known patterns
        tender_entries = re.split(r'\n(?=[A-Z].+ \(\d+/\d+\))', text.strip())
        
        # Remove header text (everything before the first tender entry)
        if len(tender_entries) > 0 and not re.search(r'^[A-Z].+ \(\d+/\d+\)', tender_entries[0]):
            tender_entries = tender_entries[1:]
        
        # Debug: Print the resulting blocks
        print("\nResulting tender blocks:")
        for i, block in enumerate(tender_entries):
            print(f"Block {i + 1}: {block}\n")
        
        print(f"Split into {len(tender_entries)} tender entries.")
        
        return tender_entries
    
    def _parse_tender_block(self, block: str) -> TenderNotice:
        """Parses a single tender block into structured data.
        
        Args:
            block: String containing a single tender notice.
            
        Returns:
            TenderNotice object containing structured tender data.
        """
        try:
            # Extract fields using improved regex patterns
            entity = re.search(r'^(.+?) \(\d+/\d+\)', block)
            org_type = re.search(r'Tipo de Órgão:(.+?) Cidade:', block)
            city = re.search(r'Cidade:\s+(.+?)\s+([A-Z]{2})', block)
            modality = re.search(r'Modalidade:\s+(.+?) Nº:', block)
            number = re.search(r'Nº:\s+([\d/]+)', block)
            obj = re.search(r'Objeto:(.+?)(?=Segmentação:|Abertura:)', block, re.DOTALL)
            segmentation = re.search(r'Segmentação:(.+?)(?=Abertura:|ID Universo:)', block, re.DOTALL)
            opening_date = re.search(r'Abertura:\s+([\d/]+\s+\d+:\d+)', block)
            tender_id = re.search(r'ID Universo:\s+(\d+)', block)
            phone = re.search(r'Telefone:\s+([\d\(\) -]+)', block)
            phone2 = re.search(r'Telefone 2:\s+([\d\(\) -]+)', block)
            access = re.search(r'Acesso:\s+(.+?)(?=Complementos:|$)', block, re.DOTALL)
            notes = re.search(r'Complementos:\s+(.+)', block, re.DOTALL)

            # Build phones list
            phones = []
            if phone and phone.group(1).strip():
                phones.append(phone.group(1).strip())
            if phone2 and phone2.group(1).strip():
                phones.append(phone2.group(1).strip())

            # Build access info list from multiline string
            access_info = []
            if access:
                access_lines = access.group(1).strip().split('\n')
                access_info = [line.strip('- ').strip() for line in access_lines if line.strip('- ').strip()]

            # Parse opening date
            parsed_date = None
            if opening_date:
                try:
                    parsed_date = datetime.strptime(opening_date.group(1).strip(), '%d/%m/%Y %H:%M')
                except ValueError:
                    logging.warning(f"Failed to parse opening date: {opening_date.group(1)}")

            # Create and return TenderNotice object
            return TenderNotice(
                organization=entity.group(1).strip() if entity else "",
                type=org_type.group(1).strip() if org_type else "",
                city=city.group(1).strip() if city else "",
                state=city.group(2).strip() if city else "",
                modality=modality.group(1).strip() if modality else "",
                number=number.group(1).strip() if number else "",
                object_description=obj.group(1).strip() if obj else "",
                segmentation=segmentation.group(1).strip() if segmentation else "",
                opening_date=parsed_date,
                id_universo=tender_id.group(1).strip() if tender_id else "",
                phones=phones,
                access_info=access_info,
                complementary_info=notes.group(1).strip() if notes else ""
            )
        except Exception as e:
            logging.error(f"Error parsing tender block: {str(e)}")
            raise
    
    def _label_tender(self, tender: TenderNotice, template: str, company_description: str) -> str:
        """Labels a tender using the LLM.
        
        Args:
            tender: TenderNotice object to label.
            template: Prompt template for labeling.
            company_description: Description of the company's business.
            
        Returns:
            Label string ('yes', 'no', or 'unsure').
        """
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
        response = self.llm.invoke(messages).content
        
        # Extract label from response
        label_match = re.search(r'(yes|no|unsure)', response.lower())
        return label_match.group(1) if label_match else 'unsure'
    
    def process_pdf(self, pdf_path: str, template: str, company_description: str) -> pd.DataFrame:
        """Processes a PDF containing tender notices.
        
        Args:
            pdf_path: Path to the PDF file.
            template: Prompt template for labeling.
            company_description: Description of the company's business.
            
        Returns:
            DataFrame containing processed and labeled tenders.
        """
        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            # Combine page contents
            text = "\n".join(page.page_content for page in pages)
            
            # Extract tender blocks
            blocks = self._extract_tender_blocks(text)
            
            # Parse blocks into TenderNotice objects
            tenders = []
            for block in blocks:
                try:
                    tender = self._parse_tender_block(block)
                    # Label tender
                    tender.label = self._label_tender(tender, template, company_description)
                    tenders.append(tender)
                except Exception as e:
                    logging.error(f"Error processing tender block: {str(e)}")
                    continue
            
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

