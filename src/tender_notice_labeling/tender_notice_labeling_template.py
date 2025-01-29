company_business_description = """
'Fast Indústria e Comércio Ltda' is a Brazilian company from the State of Santa Catarina which has become in the last decade a prominent player in the water and wastewater treatment industry.

Its contracts mostly come from public tenders, where the company competes with other companies to provide its services to the public sector.

It has experience and know-how in the design, construction, and operation of modular water and wastewater treatment plants, having already delivered several projects to clients such as Casan, Corsan, Sanepar, Sabesp, and Sanesul.

Its plants usually apply energy efficient processes such as MBBR, which may be combined with physical-chemical processes to achieve the desired treatment efficiency.

The company is technically capable of bidding on tenders for the construction of water and wastewater treatment plants of up to 1,000 L/s, or 3600 m³/h.

Fast Indústria e Comércio is particularly interested in bidding for higher quality scopes, which usually require noble materials such as stainless steel. If the tender accepts cheaper materials such as fiberglass, it is likely, although not certain, that the company will not participate in the tender, as it is not competitive in this segment.
"""

tender_notice_labeling_template = """<INSTRUCTIONS>
Based on the provided tender notice, reason through the following questions to label it as one of 'yes', 'no', or 'unsure'.

Apply 'yes' if the tender notice is clearly relevant to the company's business and the company should participate in the tender.

Apply 'no' if the tender notice is clearly irrelevant to the company's business and the company should not participate in the tender.

Apply 'unsure' if it is unclear whether the tender notice is relevant or irrelevant to the company's business and further analysis is needed to determine whether the company should participate in the tender.

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
