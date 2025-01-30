# Schema for tender notice extraction
TENDER_NOTICE_EXTRACTION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ExtractAndLabelTenderNotices",
    "description": "Schema for tender notices extracted from tender documents or emails.",
    "type": "object",
    "properties": {
        "boletins_de_licitacoes": {
            "type": "array",
            "description": "Array of published tender notices.",
            "items": {
                "type": "object",
                "properties": {
                    "num_seq_boletim": {
                        "type": "string",
                        "description": "Sequence number of the tender notice in the format ([tender_notice_seq_number]/[total_tender_notices])."
                    },
                    "orgao": {
                        "type": "string",
                        "description": "Name of the contracting organization."
                    },
                    "estado": {
                        "type": "string",
                        "description": "State abbreviation."
                    },
                    "numero_licitacao": {
                        "type": "string",
                        "description": "Tender or process identification number."
                    },
                    "objeto": {
                        "type": "string",
                        "description": "Brief description of what is being procured."
                    },
                    "data_hora_licitacao": {
                        "type": "string",
                        "description": "Date and time of tender opening."
                    },
                    "id_universo": {
                        "type": "integer",
                        "description": "The unique identifier of the tender notice."
                    },
                    "data_hora_alteracao": {
                        "type": "string",
                        "description": "Last modification date/time."
                    }
                },
                "required": [
                    "num_seq_boletim",
                    "orgao",
                    "estado",
                    "numero_licitacao",
                    "objeto",
                    "data_hora_licitacao",
                    "id_universo",
                    "data_hora_alteracao"
                ]
            }
        }
    },
    "required": [
        "boletins_de_licitacoes"
    ]
}

# Prompt template for tender notice extraction
TENDER_NOTICE_EXTRACTION_PROMPT = """The following string is a collection of tender notices extracted from an email that has been printed as a pdf. Please extract the relevant information for every single tender noteice and output a JSON object according to the provided schema.

Pay attention to the segments of the text that contain 2 sets of integers inside parentheses. These represent the current tender notice number and the total number of tender notices in the collection. Use this information in the 'num_seq_boletim" field and make sure that the last extracted tender notice is the final one. Examples: "(12/12)", "(31/31)", "(50/50)".

<tender_notices_text>
{tender_notices_text}
</tender_notices_text>
"""

# Template for tender notice labeling
TENDER_NOTICE_LABELING_TEMPLATE = """<INSTRUCTIONS>
Based on the provided tender notice, reason through the following questions to label it as one of 'yes', 'no', 'unsure' or 'insufficient_info'.

Apply 'yes' if the tender notice is likely relevant to the company's business and the company should participate in the tender. The company staff will always review the tender details before making a final decision, so do not worry too much about false positives.

Apply 'no' if the tender notice is clearly irrelevant to the company's business and the company should not participate in the tender.

Apply 'unsure' if it is unclear whether the tender notice is relevant or irrelevant to the company's business and further analysis is needed to determine whether the company should participate in the tender.

And finally, apply 'insufficient_info' if the provided tender notice does not contain enough information to make an informed recommendation. This may happen due to parsing errors or other issues with the tender notice.

VERY IMPORTANT
If the provided tender notice, for some reason (likely parsing errors upstream), does not contain enough information to make a decision, ALWAYS label it as 'unsure'.
</INSTRUCTIONS>

<COMPANY_BUSINESS_DESCRIPTION>
{company_business_description}
</COMPANY_BUSINESS_DESCRIPTION>

<TENDER_NOTICE>
{tender_notice}
</TENDER_NOTICE>
"""

# Company business description for tender notice labeling
COMPANY_BUSINESS_DESCRIPTION = """'Fast Indústria e Comércio Ltda', our USER, is a Brazilian company from the State of Santa Catarina which has become in the last decade a prominent player in the water and wastewater treatment industry.

Its contracts mostly come from public tenders, where the company competes with other companies to provide its products and services to the public sector.

It has experience and know-how in the design, construction, and operation of modular water and wastewater treatment plants, having already delivered several projects to clients such as Casan, Corsan, Sanepar, Sabesp, and Sanesul.

Its plants usually apply energy efficient processes such as MBBR, which may be combined with physical-chemical processes to achieve the desired treatment efficiency.

The company is technically capable of bidding on tenders for the construction of water and wastewater treatment plants of over 1,000 L/s (or 3600 m³/h).

Our USER also provides:
- standalone equipment for varied treatment processes, such as decanter centrifuges (which is the company's flagship product), presses, filters and others. The company is also capable of providing spare parts and technical assistance for its equipment.
- services for the operation and maintenance of water and wastewater treatment plants, particularly, but not exclusively, for plants that use MBBR technology.

Our USER does NOT independently offer or bid for the following services:
- chemical products for water and wastewater treatment.
- sludge treatment services.
- construction for civil works not related to water and wastewater treatment plants.
- civil works for water and wastewater treatment plants that are not part of a larger project that includes the supply of equipment

We are particularly interested in bidding for higher quality scopes, which usually require noble materials such as stainless steel. If the tender accepts cheaper materials such as fiberglass, it is likely, although not certain, that the company will not bid, as it is not competitive in this segment.
"""

