import asyncio
from src.tender_notice_labeling.tender_notice_processor import TenderNoticeProcessor
from src.tender_notice_labeling.tender_notice_templates import (
    TENDER_NOTICE_LABELING_TEMPLATE,
    COMPANY_BUSINESS_DESCRIPTION,
)

def progress_callback(message: str):
    print(f"\n{message}")

async def main():
    processor = TenderNoticeProcessor()
    df = await processor.process_pdf(
        'exemplos/boletins/boletins_completo.pdf',
        TENDER_NOTICE_LABELING_TEMPLATE,
        COMPANY_BUSINESS_DESCRIPTION,
        progress_callback=progress_callback
    )
    print(f'\nProcessed {len(df)} tenders')
    
    # Count labels
    label_counts = df['label'].value_counts()
    print("\nLabel distribution:")
    print(label_counts)
    
    # Show first few rows with specific columns
    print("\nFirst few rows:")
    columns = ['orgao', 'estado', 'numero_licitacao', 'objeto', 'data_hora_licitacao', 'label']
    print(df[columns].head())

if __name__ == "__main__":
    asyncio.run(main()) 

